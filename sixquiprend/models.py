from sixquiprend.sixquiprend import app, db
from sqlalchemy import func
from passlib.hash import bcrypt
import random

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
    BOT_ROLE = 1
    PLAYER_ROLE = 2
    ADMIN_ROLE = 3

    id = db.Column(db.Integer, primary_key=True)
    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=app.config['ACTIVATE_ALL_USERS'])
    urole = db.Column(db.Integer, default=PLAYER_ROLE)
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

    def is_game_owner(self, game):
        return game.users.first() == self

    def get_game_heap(self, game_id):
        return Heap.query.filter(Heap.user_id == self.id, Heap.game_id == game_id).first()

    def get_game_hand(self, game_id):
        return Hand.query.filter(Hand.user_id == self.id, Hand.game_id == game_id).first()

    def has_chosen_card(self, game_id):
        return ChosenCard.query.filter(user_id == self.id,
                game_id == game_id).count() == 1

    def get_chosen_card(self, game_id):
        return ChosenCard.query.filter(user_id == self.id,
                game_id == game_id).first()

    def choose_card_for_game(self, game_id, card_id):
        hand = self.get_game_hand(game_id)
        if card_id == None:
            index = random.randrange(len(hand.cards))
            card = hand.cards.pop(index)
        else:
            card = [card for card in hand.cards if card.id == card_id][0]
        hand.cards.remove(card)
        db.session.add(hand)
        chosen_card = ChosenCard(game_id=game_id, user_id=self.id,
            card_id=card_id)
        db.session.add(chosen_card)
        db.session.commit()
        return chosen_card

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
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_FINISHED = 2

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, nullable=False, default=STATUS_CREATED)

    def get_results(self):
        results = {}
        for user in self.users.all():
            user_game_heap = user.get_game_heap(self.id)
            results[user.username] = user_game_heap.get_value()
        return results

    def get_user(self, user_id):
        return self.users.query.get(user_id)

    def get_columns(self):
        return Column.query.filter(Column.game_id == self.id).all()

    def get_lowest_value_column(self):
        column_value = 9000
        for column in self.get_columns():
            tmp_column_value = column.get_value()
            if tmp_column_value < column_value:
                lowest_value_column = column
                column_value = tmp_column_value
            elif tmp_column_value == column_value and random.random() > 0.5:
                lowest_value_column = column
        return lowest_value_column

    def get_suitable_column(self, chosen_card):
        diff = 9000
        chosen_column = None
        for column in self.get_columns():
            last_card = sorted(column.cards, key=lambda card: card.number)[-1]
            diff_temp = chosen_card.get_card().number - last_card.number
            if diff_temp > 0 and diff_temp < diff:
                chosen_column = column
                diff = diff_temp
        if chosen_column == None:
            if chosen_card.get_user().get_urole() == User.BOT_ROLE:
                chosen_column = self.get_lowest_value_column()
                chosen_column.replace_by_card(chosen_card)
            else:
                raise NoSuitableColumnException(chosen_card.user_id)
        return chosen_column

    def resolve_turn(self):
        chosen_card = ChosenCard.query.filter(ChosenCard.game_id == self.id) \
                .join(Card) \
                .order_by(Card.number.asc()) \
                .first()
        chosen_column = self.get_suitable_column(chosen_card)
        user_game_heap = chosen_card.get_user().get_game_heap(self.id)
        if len(chosen_column.cards) == app.config['COLUMN_CARD_SIZE']:
            user_game_heap.cards += chosen_column.cards
            db.session.add(user_game_heap)
            chosen_column.cards = []
        chosen_column.cards.append(chosen_card.get_card())
        db.session.add(chosen_column)
        db.session.delete(chosen_card)
        db.session.commit()
        self.check_status()
        return [chosen_column, user_game_heap]

    def setup_game(self):
        self.status = Game.STATUS_STARTED
        card_set = list(range(1, app.config['MAX_CARD_NUMBER'] + 1))
        for user in self.users.all():
            user_hand = Hand(user_id=user.id, game_id=self.id)
            for i in range(app.config['HAND_SIZE']):
                index = random.randrange(len(card_set))
                card_number = card_set.pop(index)
                card = Card.query.filter(Card.number == card_number).first()
                user_hand.cards.append(card)
                db.session.add(user_hand)
            user_heap = Heap(user_id=user.id, game_id=self.id)
            db.session.add(user_heap)
        for i in range(app.config['BOARD_SIZE']):
            column = Column(game_id=self.id)
            index = random.randrange(len(card_set))
            card_number = card_set.pop(index)
            card = Card.query.filter(Card.number == card_number).first()
            column.cards.append(card)
            db.session.add(column)
        db.session.commit()

    def check_status(self):
        if len(self.users.first().get_game_hand(self.id).cards) == 0:
            self.status = Game.STATUS_FINISHED
            db.session.add(self)
            db.session.commit()

    def serialize(self):
        return {
                'id': self.id,
                'users': self.users.all(),
                'status': self.status
                }

column_cards = db.Table('column_cards',
        db.Column('column_id', db.Integer, db.ForeignKey('column.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=column_cards,
            backref=db.backref('columns', lazy='dynamic'))

    def replace_by_card(self, chosen_card):
        user_game_heap = chosen_card.get_user().get_game_heap(chosen_card.game_id)
        user_game_heap.cards += self.cards
        db.session.add(user_game_heap)
        self.cards = [chosen_card.get_card()]
        db.session.add(self)
        db.session.commit()

    def get_value(self):
        return sum(card.cow_value for card in self.cards)

    def serialize(self):
        return {
                'id': self.id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

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

    def get_value(self):
        return sum(card.cow_value for card in self.cards)

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

    def get_user(self):
        return User.query.get(self.user_id)

    def get_card(self):
        return Card.query.get(self.card_id)

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'card_id': self.card_id
                }
