from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from src.models.user import User
from src.models.session import Session
from src.models.payment import Payment
