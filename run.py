import os
from app import create_app
from app.models import db

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Make shell context for Flask CLI"""
    return {'db': db}

@app.cli.command()
def init_db():
    """Initialize database - create all tables"""
    db.create_all()
    print("Database initialized!")

@app.cli.command()
def drop_db():
    """Drop all database tables"""
    if input("Are you sure you want to drop all tables? (yes/no): ").lower() == 'yes':
        db.drop_all()
        print("Database dropped!")
    else:
        print("Cancelled.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
