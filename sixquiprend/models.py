from sixquiprend.sixquiprend import db
from passlib.hash import bcrypt

user_games = db.Table('user_games',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=False)
    admin = db.Column(db.Boolean, default=False)
    games = db.relationship('Game', secondary=user_games,
            backref=db.backref('users', lazy='dynamic'))

    def is_active(self):
        """Return True if the user is active."""
        return self.active

    def is_admin(self):
        """Return True if the user is admin."""
        return self.admin

    def get_id(self):
        """Return the username to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def serialize(self):
        return {'id': self.id, 'username': self.username}

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    cow_value = db.Column(db.Integer, nullable=False)

    def __init__(self, number, cow_value):
        self.number = number
        self.cow_value = cow_value

    def serialize(self):
        return {'number': self.number, 'cow_value': self.cow_value}

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def serialize(self):
        return { 'id': self.id, 'players': [u.serialize() for u in self.users.all()] }

column_cards = db.Table('column_cards',
        db.Column('column_id', db.Integer, db.ForeignKey('column.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=column_cards,
            backref=db.backref('columns', lazy='dynamic'))

hand_cards = db.Table('hand_cards',
        db.Column('hand_id', db.Integer, db.ForeignKey('hand.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Hand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=hand_cards,
            backref=db.backref('hands', lazy='dynamic'))

heap_cards = db.Table('heap_cards',
        db.Column('heap_id', db.Integer, db.ForeignKey('heap.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Heap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=heap_cards,
            backref=db.backref('heaps', lazy='dynamic'))
