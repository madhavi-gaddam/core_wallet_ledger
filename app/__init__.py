from flask import Flask
from config.config import config
from app.models import db

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from app.routes import wallet_bp
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    
    return app
