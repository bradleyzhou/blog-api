import os

from flask_migrate import Migrate
from flask_migrate import MigrateCommand

from app import db
from app import create_app
from app.models import Role
from app.models import User
from app.models import Post

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
app.cli.add_command(MigrateCommand, name='db')


@app.cli.command()
def add_admin():
    """Add a new app administrator from $ADMIN_NAME $ADMIN_EMAIL $ADMIN_KEY"""
    username = app.config['ADMIN_NAME']
    email = app.config['ADMIN_EMAIL']
    password = app.config['ADMIN_KEY']
    if not username or not email or not password:
        raise ValueError('Unable to create administrator: Insufficient information')
    Role.insert_roles()
    admin = User(username=app.config['ADMIN_NAME'],
                 email=app.config['ADMIN_EMAIL'],
                 password=app.config['ADMIN_KEY'])
    db.session.add(admin)
    db.session.commit()


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
