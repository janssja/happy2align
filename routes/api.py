"""
API routes voor Happy 2 Align
"""
from flask import Blueprint, request, jsonify, session
from src.models import db
from src.models.session import Session
from src.models.user import User
from agents.orchestrator import Orchestrator
from agents.llm_client import llm_client
import os
import traceback
import logging
import asyncio
from functools import wraps

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Initialiseer de Orchestrator met de gecentraliseerde LLM client
orchestrator = Orchestrator(llm_client.primary_llm)

# Houd sessie state bij
session_states = {}

@api_bp.route('/process', methods=['POST'])
def process_input():
    """Verwerk een bericht via de orchestrator met sessie state management"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Geen bericht ontvangen'}), 400
        
        message = data['message']
        session_id = data.get('session_id', 'default')
        
        # Haal sessie state op
        if session_id not in session_states:
            session_states[session_id] = {
                'history': [],
                'current_workflow': None,
                'requirements': [],
                'current_subtopic': 0,
                'current_question': 0,
                'subtopics': None,
                'state': 'initial'  # initial, collecting_requirements, workflow_generated
            }
        
        state = session_states[session_id]
        
        # Voeg het bericht toe aan de geschiedenis
        state['history'].append({"role": "user", "content": message})
        
        # Bepaal wat we moeten doen op basis van de state
        if state['state'] == 'collecting_requirements' and state['subtopics']:
            # We zijn requirements aan het verzamelen
            result = await_handle_requirement_answer(session_id, message)
        else:
            # Laat de orchestrator beslissen
            result = orchestrator.run_conversation(
                message, 
                conversation_history=state['history'],
                current_workflow=state['current_workflow']
            )
        
        # Update state op basis van result
        if result.get('type') == 'question':
            state['state'] = 'collecting_requirements'
            if not state['subtopics']:
                # First time, store subtopics (zou van orchestrator moeten komen)
                state['subtopics'] = result.get('subtopics', [])
            state['current_subtopic'] = result.get('subtopic_index', 0)
            state['current_question'] = result.get('question_index', 0)
            
            # Voeg de vraag toe aan de geschiedenis
            state['history'].append({"role": "assistant", "content": result['question']})
            
        elif result.get('type') == 'workflow':
            state['state'] = 'workflow_generated'
            state['current_workflow'] = result.get('workflow', [])
            state['requirements'] = result.get('requirements', [])
            
        elif result.get('type') == 'workflow_refined':
            state['current_workflow'] = result.get('workflow', [])
        
        # Voeg response toe aan geschiedenis
        if result.get('type') != 'question' and 'response' in result:
            state['history'].append({"role": "assistant", "content": result['response']})
        
        # Bereid response voor frontend
        response_data = {
            'response': result.get('question') if result.get('type') == 'question' else format_response(result),
            'type': result.get('type', 'unknown'),
            'context': {
                'state': state['state'],
                'current_subtopic': state['current_subtopic'],
                'current_question': state['current_question'],
                'has_workflow': state['current_workflow'] is not None,
                'requirements_count': len(state['requirements'])
            }
        }
        
        # Voeg extra info toe indien beschikbaar
        if result.get('expertise'):
            response_data['expertise'] = result['expertise']
        if result.get('sentiment'):
            response_data['sentiment'] = result['sentiment']
        if result.get('workflow'):
            response_data['workflow'] = result['workflow']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in process_input: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Fout bij het verwerken van het bericht: {str(e)}',
            'type': 'error'
        }), 500

def await_handle_requirement_answer(session_id: str, answer: str) -> dict:
    """
    Handle een antwoord tijdens requirement collection
    """
    state = session_states[session_id]
    
    # Sla het antwoord op
    if 'answers' not in state:
        state['answers'] = []
    state['answers'].append({
        'subtopic': state['subtopics'][state['current_subtopic']]['title'],
        'question_index': state['current_question'],
        'answer': answer
    })
    
    # Bepaal volgende stap
    current_subtopic = state['subtopics'][state['current_subtopic']]
    
    # Zijn er nog vragen voor dit subtopic?
    if state['current_question'] < len(current_subtopic['questions']) - 1 and state['current_question'] < 4:
        state['current_question'] += 1
        next_question = current_subtopic['questions'][state['current_question']]
        
        # Vraag verfijnen met ToM
        return {
            'type': 'question',
            'question': next_question,  # In productie: gebruik orchestrator om te verfijnen
            'subtopic': current_subtopic['title'],
            'subtopic_index': state['current_subtopic'],
            'question_index': state['current_question']
        }
    
    # Zijn er nog subtopics?
    elif state['current_subtopic'] < len(state['subtopics']) - 1:
        state['current_subtopic'] += 1
        state['current_question'] = 0
        next_subtopic = state['subtopics'][state['current_subtopic']]
        next_question = next_subtopic['questions'][0]
        
        return {
            'type': 'question',
            'question': next_question,  # In productie: gebruik orchestrator om te verfijnen
            'subtopic': next_subtopic['title'],
            'subtopic_index': state['current_subtopic'],
            'question_index': 0
        }
    
    # Alle vragen beantwoord, genereer workflow
    else:
        # Formatteer requirements van answers
        requirements = []
        for answer_data in state.get('answers', []):
            requirements.append({
                'subtopic': answer_data['subtopic'],
                'answer': answer_data['answer']
            })
        
        # Gebruik orchestrator om workflow te genereren
        result = orchestrator.run_conversation(
            "Generate workflow based on collected requirements",
            conversation_history=state['history'],
            current_workflow=None
        )
        
        # Update state
        state['state'] = 'workflow_generated'
        state['requirements'] = requirements
        
        return result

def format_response(result: dict) -> str:
    """Format het resultaat voor de frontend"""
    if result.get('type') == 'workflow':
        workflow = result.get('workflow', [])
        response = "Hier is je gegenereerde workflow:\n\n"
        for i, step in enumerate(workflow, 1):
            response += f"{i}. {step}\n"
        return response
    
    elif result.get('type') == 'workflow_refined':
        workflow = result.get('workflow', [])
        response = "Je workflow is aangepast:\n\n"
        for i, step in enumerate(workflow, 1):
            response += f"{i}. {step}\n"
        return response
    
    elif result.get('type') == 'error':
        return f"Er is een fout opgetreden: {result.get('error', 'Onbekende fout')}"
    
    else:
        return result.get('response', 'Geen response beschikbaar')

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Geef de status van de huidige sessie"""
    session_id = request.args.get('session_id', 'default')
    
    if session_id not in session_states:
        return jsonify({
            'status': 'no_session',
            'message': 'Geen actieve sessie'
        })
    
    state = session_states[session_id]
    
    return jsonify({
        'status': 'active',
        'state': state['state'],
        'progress': {
            'current_subtopic': state['current_subtopic'],
            'total_subtopics': len(state.get('subtopics', [])),
            'current_question': state['current_question'],
            'requirements_collected': len(state.get('requirements', [])),
            'has_workflow': state['current_workflow'] is not None
        }
    })

@api_bp.route('/reset', methods=['POST'])
def reset_session():
    """Reset de sessie"""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id in session_states:
        del session_states[session_id]
    
    return jsonify({
        'status': 'reset',
        'message': 'Sessie gereset'
    })