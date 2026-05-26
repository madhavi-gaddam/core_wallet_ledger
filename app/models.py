from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum as PyEnum

db = SQLAlchemy()

class TransactionType(PyEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    wallet = db.relationship('Wallet', uselist=False, backref='user', cascade='all, delete-orphan')
    transactions = db.relationship('Ledger', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Wallet(db.Model):
    """Wallet model - one wallet per user"""
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Wallet user_id={self.user_id}, balance={self.balance}>'

class Ledger(db.Model):
    """Transaction ledger - tracks all wallet transactions"""
    __tablename__ = 'ledger'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # CREDIT or DEBIT
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    balance_before = db.Column(db.Numeric(15, 2), nullable=False)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ledger user_id={self.user_id}, type={self.transaction_type}, amount={self.amount}>'
