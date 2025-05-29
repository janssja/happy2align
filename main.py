"""
Main application entry point for Happy 2 Align
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from src.models import db
from src.routes import register_blueprints
import secrets

def create_app():
    """Creëer en configureer de Flask applicatie."""
    app = Flask(__name__)
    
    # Configuratie
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'happy2align.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Uncomment voor MySQL in productie
    # app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'happy2align')}"
    
    # Initialiseer database
    db.init_app(app)
    
    # Registreer blueprints
    register_blueprints(app)
    
    # Creëer database tabellen
    with app.app_context():
        print('Creating database tables...')
        db.create_all()
        print('Database tables created!')
    
    # Routes
    @app.route('/')
    def index():
        """Homepage route."""
        if 'user_id' in session:
            return redirect(url_for('dashboard.get_sessions'))
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Use port 5001 instead of 5000 to avoid conflicts with AirPlay
    app.run(debug=True, port=5001)
