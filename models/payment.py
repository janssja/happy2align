from datetime import datetime
from src.models import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(64), nullable=False)
    transaction_id = db.Column(db.String(128), nullable=True)
    
    def __init__(self, user_id, amount, credits, payment_method, transaction_id=None):
        self.user_id = user_id
        self.amount = amount
        self.credits = credits
        self.payment_method = payment_method
        self.transaction_id = transaction_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'credits': self.credits,
            'payment_date': self.payment_date.isoformat(),
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id
        }
    
    def __repr__(self):
        return f'<Payment {self.id}>'
