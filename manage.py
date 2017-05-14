import os

from flask_migrate import Migrate
from flask_migrate import MigrateCommand

from app import db
from app import create_app
from app.models import Role
from app.models import User

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

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
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()
