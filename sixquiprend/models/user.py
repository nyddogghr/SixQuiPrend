from passlib.hash import bcrypt
from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.sixquiprend import app, db
import random

user_games = db.Table('user_games',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
)

class User(db.Model):
    ROLE_BOT = 0
    PLAYER_ROLE = 1
    ROLE_ADMIN = 2

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=app.config['ACTIVATE_ALL_USERS'])
    urole = db.Column(db.Integer, default=PLAYER_ROLE)
    chosen_cards = db.relationship('ChosenCard', backref='user', lazy='dynamic',
            cascade="all, delete, delete-orphan")
    hands = db.relationship('Hand', backref='user', lazy='dynamic',
            cascade="all, delete, delete-orphan")
    heaps = db.relationship('Heap', backref='user', lazy='dynamic',
            cascade="all, delete, delete-orphan")
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
            if user.urole == User.ROLE_BOT:
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
