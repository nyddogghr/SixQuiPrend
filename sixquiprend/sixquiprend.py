from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , sixquiprend.py

from sixquiprend.config import *

db = SQLAlchemy(app)

from sixquiprend.utils import *
from sixquiprend.models import *
from sixquiprend.routes import *

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return User.query.filter(User.username == username).first()
