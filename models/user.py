"""
User model for Happy 2 Align
"""

from datetime import datetime
from src.models import db

class User(db.Model):
    """User model for authentication and user management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    credits_remaining = db.Column(db.Integer, default=1)  # 1 gratis sessie voor nieuwe gebruikers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaties
    sessions = db.relationship('Session', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'credits_remaining': self.credits_remaining,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat()
        }
    
    def add_credits(self, amount):
        self.credits_remaining += amount
        
    def use_credit(self):
        if self.credits_remaining > 0:
            self.credits_remaining -= 1
            return True
        return False
