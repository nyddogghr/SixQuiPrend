from passlib.hash import bcrypt
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.sixquiprend import app, db
import random

user_games = db.Table('user_games',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")),
        db.Column('game_id', db.Integer, db.ForeignKey('game.id', ondelete="CASCADE"))
)

class User(db.Model):
    BOT_ROLE = 1
    PLAYER_ROLE = 2
    ADMIN_ROLE = 3

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=app.config['ACTIVATE_ALL_USERS'])
    urole = db.Column(db.Integer, default=PLAYER_ROLE)
    games = db.relationship('Game', secondary=user_games,
            backref=db.backref('users', lazy='dynamic'))

    ################################################################################
    ## Getters
    ################################################################################

    def find(user_id):
        user = User.query.get(user_id)
        if not user:
            raise SixQuiPrendException('User doesn\'t exist', 404)
        return user

    def is_active(self):
        return self.active

    def get_urole(self):
        return self.urole

    def get_id(self):
        """Return the username to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def is_game_owner(self, game):
        return game.owner_id == self.id

    def get_game_heap(self, game_id):
        return Heap.query.filter(Heap.game_id == game_id, Heap.user_id == self.id).first()

    def get_game_hand(self, game_id):
        return Hand.query.filter(Hand.game_id == game_id, Hand.user_id == self.id).first()

    def has_chosen_card(self, game_id):
        return self.get_chosen_card(game_id) != None

    def get_chosen_card(self, game_id):
        return ChosenCard.query.filter(game_id == game_id,
                ChosenCard.user_id == self.id).first()

    ################################################################################
    ## Actions
    ################################################################################

    def delete(user_id):
        user = User.find(user_id)
        db.session.delete(user)
        db.session.commit()

    def register(username, password):
        user = User.query.filter(User.username == username).first()
        if not user:
            user = User(username=username, password=bcrypt.hash(password))
            db.session.add(user)
            db.session.commit()
            return user
        else:
            raise SixQuiPrendException('User already exists', 400)

    def login(username, password):
        user = User.query.filter(User.username == username).first()
        if user:
            if user.urole == User.BOT_ROLE:
                raise SixQuiPrendException('Bots cannot login', 403)
            if not user.is_active():
                raise SixQuiPrendException('User is inactive', 403)
            if user.verify_password(password):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                return user
            else:
                raise SixQuiPrendException('Password is invalid', 400)
        else:
            raise SixQuiPrendException('User doesn\'t exist', 404)

    def logout(self):
        self.authenticated = False
        db.session.add(self)
        db.session.commit()

    def change_active(self, active):
        self.active = active
        db.session.add(self)
        db.session.commit()

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        return {
                'id': self.id,
                'username': self.username,
                'urole': self.urole,
                }
