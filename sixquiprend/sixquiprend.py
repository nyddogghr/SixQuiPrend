from flask import Flask
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , sixquiprend.py

from sixquiprend.config import *

db = SQLAlchemy(app)

from sixquiprend.utils import *
from sixquiprend.models.card import Card
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.column import Column
from sixquiprend.models.game import Game
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.models.user import User
from functools import wraps

def admin_required(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.get_urole() < User.ADMIN_ROLE:
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return func_wrapper

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

class MyJSONEncoder(JSONEncoder):
    def default(self, obj):
        return obj.serialize()

app.json_encoder = MyJSONEncoder

@login_manager.user_loader
def load_user(username):
    return User.query.filter(User.username == username).first()

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify(error='Unauthorized'), 401

@app.errorhandler(SixQuiPrendException)
def _(error):
    return jsonify(error=error.message), error.code

from sixquiprend.routes.games import *
from sixquiprend.routes.games_data import *
from sixquiprend.routes.games_turn import *
from sixquiprend.routes.login_logout import *
from sixquiprend.routes.templates import *
from sixquiprend.routes.users import *
