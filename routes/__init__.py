"""
Routes package for Happy 2 Align
"""

from flask import Blueprint

# Importeer alle blueprints
from src.routes.auth import auth_bp
from src.routes.dashboard import dashboard_bp
from src.routes.payment import payment_bp
from .api import api_bp
from .chat import chat_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(chat_bp)
