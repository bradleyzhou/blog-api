import os

from flask_migrate import Migrate
from flask_migrate import MigrateCommand

from app import db
from app import create_app
from app.models import User
from app.models import Post

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
app.cli.add_command(MigrateCommand, name='db')
