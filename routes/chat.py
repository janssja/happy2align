"""
Routes voor de chat functionaliteit
"""

from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

chat_bp = Blueprint('chat', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@chat_bp.route('/chat')
@login_required
def index():
    """Render de chat interface"""
    return render_template('chat.html') 