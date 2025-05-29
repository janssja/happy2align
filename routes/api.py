"""
API routes voor Happy 2 Align
"""

from flask import Blueprint, request, jsonify
from src.models import db
from src.models.session import Session
from src.models.user import User
from agents.router_agent import RouterAgent
from agents.requirement_refiner import RequirementRefiner
from agents.workflow_generator import WorkflowGenerator
from agents.manager import AgentManager
from agents.orchestrator import Orchestrator
from langchain_community.chat_models import ChatOpenAI
import asyncio
import traceback

api_bp = Blueprint('api', __name__)

# Initialiseer de agents
router = RouterAgent()
requirement_refiner = RequirementRefiner()
workflow_generator = WorkflowGenerator()

# Initialiseer de centrale manager
manager = AgentManager()

# Initialiseer de Orchestrator met een LLM
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
orchestrator = Orchestrator(llm)

def run_async(coro):
    """Helper functie om async code uit te voeren in Flask"""
    try:
        return asyncio.run(coro)
    except Exception as e:
        print(f"Error in run_async: {str(e)}")
        print(traceback.format_exc())
        raise

@api_bp.route('/process', methods=['POST'])
def process_input():
    """Verwerk een bericht en geef een response terug via de orchestrator"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Geen bericht ontvangen'}), 400
        message = data['message']
        history = data.get('history', [])
        current_workflow = data.get('workflow', None)
        print(f"[API] Ontvangen history: {history}")
        result = orchestrator.run_conversation(message, conversation_history=history, current_workflow=current_workflow)
        return jsonify(result)
    except Exception as e:
        print(f"[API] Fout bij het verwerken van requirements: {e}")
        return jsonify({'error': f'Fout bij het verwerken van requirements: {str(e)}'}), 500

@api_bp.route('/subtopics', methods=['POST'])
def generate_subtopics():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Geen JSON data ontvangen'}), 400
            
        user_id = request.session.get('user_id')
        session_id = data.get('session_id')
        topic = data.get('topic')
        
        if not session_id or not topic:
            return jsonify({'error': 'Ontbrekende parameters'}), 400
        
        # Haal sessie op
        user_session = Session.query.filter_by(id=session_id, user_id=user_id).first()
        if not user_session:
            return jsonify({'error': 'Sessie niet gevonden'}), 404
        
        try:
            # Genereer subtopics met agent manager
            response = run_async(agent_manager.process_query(f"Generate subtopics for: {topic}"))
            
            # Update sessie met subtopics
            user_session.set_subtopics(response)
            db.session.commit()
            
            return jsonify({
                'subtopics': response
            })
        except Exception as e:
            print(f"Error in generate_subtopics: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Fout bij het genereren van subtopics: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error in generate_subtopics: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@api_bp.route('/expertise', methods=['POST'])
def estimate_expertise():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Geen JSON data ontvangen'}), 400
            
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({'error': 'Ontbrekende parameters'}), 400
        
        try:
            # Schat expertise in met agent manager
            response = run_async(agent_manager.process_query(f"Estimate expertise level for: {user_query}"))
            
            return jsonify({
                'expertise_level': response
            })
        except Exception as e:
            print(f"Error in estimate_expertise: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Fout bij het inschatten van expertise: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error in estimate_expertise: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@api_bp.route('/sentiment', methods=['POST'])
def detect_sentiment():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Geen JSON data ontvangen'}), 400
            
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({'error': 'Ontbrekende parameters'}), 400
        
        try:
            # Detecteer sentiment met agent manager
            response = run_async(agent_manager.process_query(f"Detect sentiment for: {user_query}"))
            
            return jsonify({
                'sentiment': response
            })
        except Exception as e:
            print(f"Error in detect_sentiment: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Fout bij het detecteren van sentiment: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error in detect_sentiment: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Geef de actuele status van alle agenten terug."""
    try:
        return jsonify(manager.get_status())
    except Exception as e:
        print(f"[API] Fout bij ophalen status: {e}")
        return jsonify({'error': f'Fout bij ophalen status: {str(e)}'}), 500
