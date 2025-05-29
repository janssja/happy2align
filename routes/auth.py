"""
Authentication routes for Happy 2 Align
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db
from src.models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Niet ingelogd'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Valideer input
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Ontbrekende velden'}), 400
        
        # Controleer of gebruiker al bestaat
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email adres is al in gebruik'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Gebruikersnaam is al in gebruik'}), 400
        
        # Hash het wachtwoord
        password_hash = generate_password_hash(data['password'])
        
        # Maak nieuwe gebruiker
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash
        )
        
        # Sla op in database
        db.session.add(user)
        db.session.commit()
        
        # Log gebruiker in
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Registratie succesvol',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Valideer input
        if not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Ontbrekende velden'}), 400
        
        # Zoek gebruiker
        user = User.query.filter_by(email=data['email']).first()
        
        # Controleer wachtwoord
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Ongeldige inloggegevens'}), 401
        
        # Log gebruiker in
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Login succesvol',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict()), 200
