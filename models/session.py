from datetime import datetime
import json
from src.models import db

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    topic = db.Column(db.String(256), nullable=True)
    subtopics = db.Column(db.Text, nullable=True)  # JSON string
    requirements = db.Column(db.Text, nullable=True)  # JSON string
    workflow = db.Column(db.Text, nullable=True)  # JSON string
    status = db.Column(db.String(32), default='active')  # active, completed, failed
    
    def __init__(self, user_id, topic=None):
        self.user_id = user_id
        self.topic = topic
    
    def set_subtopics(self, subtopics):
        self.subtopics = json.dumps(subtopics)
    
    def get_subtopics(self):
        if self.subtopics:
            return json.loads(self.subtopics)
        return []
    
    def set_requirements(self, requirements):
        self.requirements = json.dumps(requirements)
    
    def get_requirements(self):
        if self.requirements:
            return json.loads(self.requirements)
        return []
    
    def set_workflow(self, workflow):
        self.workflow = json.dumps(workflow)
    
    def get_workflow(self):
        if self.workflow:
            return json.loads(self.workflow)
        return []
    
    def complete(self):
        self.status = 'completed'
        self.end_time = datetime.utcnow()
    
    def fail(self):
        self.status = 'failed'
        self.end_time = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'topic': self.topic,
            'subtopics': self.get_subtopics(),
            'requirements': self.get_requirements(),
            'workflow': self.get_workflow(),
            'status': self.status
        }
    
    def __repr__(self):
        return f'<Session {self.id}>'
