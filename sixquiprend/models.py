from sixquiprend.sixquiprend import db
from passlib.hash import bcrypt
import math

class NoSuitableColumnException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return 'User %i must choose a column to replace', value

user_games = db.Table('user_games',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
)

class User(db.Model):
    USER_BOT_ROLE = 1
    USER_PLAYER_ROLE = 2
    USER_ADMIN_ROLE = 3

    id = db.Column(db.Integer, primary_key=True)
    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=False)
    urole = db.Column(db.Integer, default=USER_PLAYER_ROLE)
    games = db.relationship('Game', secondary=user_games,
            backref=db.backref('users', lazy='dynamic'))

    def is_active(self):
        """Return True if the user is active."""
        return self.active

    def get_urole(self):
        """Return urole index if the user is admin."""
        return self.urole

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
        return {
                'id': self.id,
                'username': self.username,
                'urole': self.urole
                }

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    cow_value = db.Column(db.Integer, nullable=False)

    def __init__(self, number, cow_value):
        self.number = number
        self.cow_value = cow_value

    def serialize(self):
        return {
                'id': self.id,
                'number': self.number,
                'cow_value': self.cow_value
                }

class Game(db.Model):
    GAME_STATUS_CREATED = 0
    GAME_STATUS_STARTED = 1
    GAME_STATUS_FINISHED = 2

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, nullable=False, default=GAME_STATUS_CREATED)

    def serialize(self):
        return {
                'id': self.id,
                'users': self.users.all(),
                'status': self.status
                }

    def resolve_turn(self, turn_number):
        chosen_card = self.chosen_cards \
                .join(cards, chosen_cards.card_id==cards.id) \
                .order_by(model.Card.number.asc()).first()
        diff = 104
        user_game_heap_changed = False
        for column in self.columns.all():
            last_card = columns.cards.order_by(model.Card.number.asc()).last()
            diff_temp = chosen_card.number - last_card.number
            if diff_temp > 0 and diff_temp < diff:
                diff = diff_temp
                chosen_column = column
        if diff == 104:
            if chosen_card.user.get_urole() == User.USER_ROLE_BOT:
                chosen_column = columns.first()
                user_game_heap = chosen_column.replace_by_card(chosen_card)
                return [chosen_column, user_game_heap]
            else:
                raise NoSuitableColumnException(chosen_card.user_id)
        if chosen_column.cards.count() == 5:
            user_game_heap = chosen_card.user.heaps.query \
                    .filter(game_id=self.id).first()
            user_game_heap.cards.append(chosen_column.cards)
            db.session.add(user_game_heap)
            chosen_column.cards = []
            db.session.add(chosen_column)
            db.session.commit()
            user_game_heap_changed = True
        chosen_column.cards.append(chosen_cards.card)
        db.session.add(chosen_column)
        db.session.delete(chosen_card)
        db.session.commit()
        if user_game_heap_changed == True:
            return [chosen_column, user_game_heap]
        else:
            return chosen_column



column_cards = db.Table('column_cards',
        db.Column('column_id', db.Integer, db.ForeignKey('column.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=column_cards,
            backref=db.backref('columns', lazy='dynamic'))

    def serialize(self):
        return {
                'id': self.id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

    def replace_by_card(self, chosen_card):
        user_heap = chosen_card.user.heaps.query \
                .filter(game_id=chosen_card.game_id).first()
        user_heap.cards.appen(self.cards)
        db.session.add(user_heap)
        self.cards = chosen_card.card
        db.session.add(self)
        db.session.delete(chosen_card)
        db.session.commit()
        return user_heap

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

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

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

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

class ChosenCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'card_id': self.card_id
                }
