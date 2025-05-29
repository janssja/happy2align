from flask import Blueprint, request, jsonify, session, render_template
from src.models import db
from src.models.session import Session
from src.models.user import User
from functools import wraps
import json

dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Niet ingelogd'}), 401
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    user_id = session['user_id']
    user_sessions = Session.query.filter_by(user_id=user_id).all()
    
    # Bepaal of het een API-call is of een browser-request
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            'sessions': [s.to_dict() for s in user_sessions]
        })
    else:
        return render_template('dashboard/sessions.html')

@dashboard_bp.route('/sessions/<int:session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    user_id = session['user_id']
    user_session = Session.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not user_session:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
    
    return jsonify(user_session.to_dict())

@dashboard_bp.route('/sessions/new', methods=['POST'])
@login_required
def create_session():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Controleer of gebruiker voldoende credits heeft
    if user.credits_remaining <= 0:
        return jsonify({
            'error': 'Onvoldoende credits',
            'message': 'Je hebt geen credits meer. Koop meer credits om door te gaan.'
        }), 403
    
    data = request.get_json()
    topic = data.get('topic', 'Nieuwe sessie')
    
    # Maak nieuwe sessie aan
    new_session = Session(user_id=user_id, topic=topic)
    db.session.add(new_session)
    
    # Gebruik een credit
    user.use_credit()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Sessie aangemaakt',
        'session': new_session.to_dict(),
        'credits_remaining': user.credits_remaining
    }), 201

@dashboard_bp.route('/sessions/<int:session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    user_id = session['user_id']
    user_session = Session.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not user_session:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
    
    user_session.complete()
    db.session.commit()
    
    return jsonify({
        'message': 'Sessie voltooid',
        'session': user_session.to_dict()
    })

@dashboard_bp.route('/credits', methods=['GET'])
@login_required
def get_credits():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    return jsonify({
        'credits_remaining': user.credits_remaining
    })
