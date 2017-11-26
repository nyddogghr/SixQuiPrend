from sixquiprend.models.card import Card
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.column import Column
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
import random

class Game(db.Model):
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_FINISHED = 2

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, nullable=False, default=STATUS_CREATED)
    is_resolving_turn = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hands = db.relationship('Hand', backref='game', lazy='dynamic',
            cascade="all, delete, delete-orphan")
    heaps = db.relationship('Heap', backref='game', lazy='dynamic',
            cascade="all, delete, delete-orphan")
    columns = db.relationship('Column', backref='game', lazy='dynamic',
            cascade="all, delete, delete-orphan")
    chosen_cards = db.relationship('ChosenCard', backref='game', lazy='dynamic',
            cascade="all, delete, delete-orphan")

    ################################################################################
    ## Getters
    ################################################################################

    def find(game_id):
        game = Game.query.get(game_id)
        if not game:
            raise SixQuiPrendException('Game doesn\'t exist', 404)
        return game

    def find_user(self, user_id):
        user = self.users.filter(User.id==user_id).first()
        if not user:
            raise SixQuiPrendException('User not in game', 404)
        return user

    def find_column(self, column_id):
        column = self.columns.filter(Column.id == column_id).first()
        if not column:
            raise SixQuiPrendException('Column not found', 404)
        return column

    def find_chosen_card(self, user_id):
        chosen_card = self.chosen_cards.filter(ChosenCard.user_id ==
                user_id).first()
        if not chosen_card:
            raise SixQuiPrendException('Chosen card not found', 404)
        return chosen_card

    def get_user_hand(self, user_id):
        user = self.find_user(user_id)
        hand = self.hands.filter(Hand.user_id == user.id).first()
        return hand

    def get_user_heap(self, user_id):
        user = self.find_user(user_id)
        heap = self.heaps.filter(Heap.user_id == user.id).first()
        return heap

    def get_user_status(self, user_id):
        user = self.find_user(user_id)
        user_dict = user.serialize()
        user_dict['has_chosen_card'] = self.get_user_chosen_card(user_id) != None
        user_dict['needs_to_choose_column'] = self.user_needs_to_choose_column(user_id)
        return user_dict

    def get_user_chosen_card(self, user_id):
        return self.chosen_cards.filter(ChosenCard.user_id == user_id).first()

    def check_is_started(self):
        if self.status != Game.STATUS_STARTED:
            raise SixQuiPrendException('Game not started', 400)

    def check_is_owner(self, user_id):
        if self.owner_id != user_id:
            raise SixQuiPrendException('User is not game owner', 403)

    def get_results(self):
        results = {}
        if self.status == Game.STATUS_CREATED:
            return results
        for user in self.users.all():
            user_game_heap = self.get_user_heap(user.id)
            results[user.username] = user_game_heap.get_value()
        return results

    def get_lowest_value_column(self):
        column_value = 9000
        for column in self.columns:
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
        for column in self.columns:
            last_card = sorted(column.cards, key=lambda card: card.number)[-1]
            diff_temp = chosen_card.card.number - last_card.number
            if diff_temp > 0 and diff_temp < diff:
                chosen_column = column
                diff = diff_temp
        if chosen_column == None:
            raise SixQuiPrendException('User ' + str(chosen_card.user_id) + ' must choose a column', 422)
        return chosen_column

    def get_available_bots(self):
        bots = User.query.filter(User.urole == User.ROLE_BOT).order_by(User.id).all()
        available_bots = []
        for bot in bots:
            if not bot in self.users.all():
                available_bots.append(bot)
        return available_bots

    def get_chosen_cards_for_current_user(self, current_user_id):
        if not self.is_resolving_turn:
            chosen_cards = self.chosen_cards.filter(ChosenCard.user_id == current_user_id)
            if chosen_cards.count() == 0:
                raise SixQuiPrendException('You haven\'t chosen a card', 400)
        return self.chosen_cards.all()

    def user_needs_to_choose_column(self, user_id):
        self.check_is_started()
        user = self.find_user(user_id)
        if self.get_user_chosen_card(user_id) == None:
            return False
        cc = self.get_user_chosen_card(user_id)
        try:
            self.get_suitable_column(cc)
        except SixQuiPrendException:
            lower_chosen_card_count = self.chosen_cards.join(Card) \
                    .filter(Card.number < cc.card.number) \
                    .count()
            return lower_chosen_card_count == 0
        return False

    def can_place_card(self, current_user_id):
        self.check_is_owner(current_user_id)
        if self.status != Game.STATUS_STARTED:
            return False
        if self.is_resolving_turn:
            chosen_card = self.chosen_cards.join(Card).order_by(Card.number.asc()).first()
            if chosen_card.user.urole != User.ROLE_BOT:
                if self.user_needs_to_choose_column(chosen_card.user_id):
                    return False
            return True
        if self.chosen_cards.count() == self.users.count():
            return True
        return False

    def can_choose_cards_for_bots(self, current_user_id):
        if self.can_place_card(current_user_id):
            return False
        for bot in self.users.filter(User.urole == User.ROLE_BOT).all():
            if self.get_user_chosen_card(bot.id) == None:
                return True
        return False

    ################################################################################
    ## Actions
    ################################################################################

    def create(user):
        game = Game(status=Game.STATUS_CREATED)
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        return game

    def delete(game_id):
        game = Game.find(game_id)
        db.session.delete(game)
        db.session.commit()

    def setup(self, current_user_id):
        self.check_is_owner(current_user_id)
        if self.status != Game.STATUS_CREATED:
            raise SixQuiPrendException('Can only start a created game', 400)
        if self.users.count() < 2:
            raise SixQuiPrendException('Cannot start game with less than 2 players', 400)
        self.status = Game.STATUS_STARTED
        card_set = list(range(1, app.config['MAX_CARD_NUMBER'] + 1))
        for user in self.users.all():
            user_hand = Hand(game_id=self.id, user_id=user.id)
            for i in range(app.config['HAND_SIZE']):
                index = random.randrange(len(card_set))
                card_number = card_set.pop(index)
                card = Card.query.filter(Card.number == card_number).first()
                user_hand.cards.append(card)
                db.session.add(user_hand)
            user_heap = Heap(game_id=self.id, user_id=user.id)
            db.session.add(user_heap)
        for i in range(app.config['BOARD_SIZE']):
            column = Column(game_id=self.id)
            index = random.randrange(len(card_set))
            card_number = card_set.pop(index)
            card = Card.query.filter(Card.number == card_number).first()
            column.cards.append(card)
            db.session.add(column)
        db.session.add(self)
        db.session.commit()

    def add_user(self, user):
        if self.status != Game.STATUS_CREATED:
            raise SixQuiPrendException('Cannot enter an already started game', 400)
        if self.users.count() == app.config['MAX_PLAYER_NUMBER']:
            max_number = str(app.config['MAX_PLAYER_NUMBER'])
            error = 'Game has already ' + max_number + ' players'
            raise SixQuiPrendException(error, 400)
        if user in self.users.all():
            raise SixQuiPrendException('Cannot enter twice in a game', 400)
        self.users.append(user)
        db.session.add(self)
        db.session.commit()

    def add_bot(self, bot_id, current_user_id):
        self.check_is_owner(current_user_id)
        bot = User.find(bot_id)
        if bot.get_urole() != User.ROLE_BOT:
            raise SixQuiPrendException('Can only add a bot', 400)
        self.add_user(bot)

    def remove_user(self, user):
        if user not in self.users.all():
            raise SixQuiPrendException('Not in game', 400)
        if user.is_game_owner(self):
            self.remove_owner(user.id)
        db.session.delete(self.get_user_hand(user.id))
        db.session.delete(self.get_user_heap(user.id))
        if self.get_user_chosen_card(user.id):
            db.session.delete(self.get_user_chosen_card(user.id))
        self.users.remove(user)
        db.session.add(self)
        db.session.commit()

    def remove_owner(self, user_id):
        if self.owner_id != user_id:
            raise SixQuiPrendException('User is not game owner', 400)
        new_owner = self.users.filter(User.id != user_id,
                User.urole != User.ROLE_BOT).first()
        if not new_owner:
            raise SixQuiPrendException('There is no other non-bot player', 400)
        else:
            self.owner_id = new_owner.id
            db.session.add(self)
            db.session.commit()

    def place_card(self, current_user_id):
        self.check_is_started()
        if not self.can_place_card(current_user_id):
            raise SixQuiPrendException('No chosen card to place', 422)
        chosen_card = self.chosen_cards.join(Card).order_by(Card.number.asc()).first()
        user_game_heap = self.get_user_heap(chosen_card.user_id)
        try:
            chosen_column = self.get_suitable_column(chosen_card)
            if len(chosen_column.cards) == app.config['COLUMN_CARD_SIZE']:
                user_game_heap.cards += chosen_column.cards
                db.session.add(user_game_heap)
                chosen_column.cards = []
            chosen_column.cards.append(chosen_card.card)
            db.session.add(chosen_column)
            db.session.delete(chosen_card)
            db.session.commit()
        except SixQuiPrendException as e:
            if chosen_card.user.urole == User.ROLE_BOT:
                chosen_column = self.get_lowest_value_column()
                chosen_column.replace_by_card(chosen_card)
            else:
                raise e
        self.update_status()
        return [chosen_column, user_game_heap]

    def choose_cards_for_bots(self, current_user_id):
        self.check_is_owner(current_user_id)
        self.check_is_started()
        if self.is_resolving_turn:
            raise SixQuiPrendException('Cannot choose cards for bots while card \
            is being placed', 400)
        if not self.can_choose_cards_for_bots(current_user_id):
            raise SixQuiPrendException('Bots have already chosen cards', 400)
        for bot in self.users.filter(User.urole == User.ROLE_BOT).order_by(User.id).all():
            if self.get_user_chosen_card(bot.id) == None:
                self.choose_card_for_user(bot.id)
        db.session.add(self)
        db.session.commit()

    def choose_card_for_user(self, user_id, card_id=None):
        self.check_is_started()
        user = self.find_user(user_id)
        if self.is_resolving_turn:
            raise SixQuiPrendException('Cannot choose a card while resolving a turn', 400)
        if self.get_user_chosen_card(user_id):
            raise SixQuiPrendException('User has already chosen a card', 400)
        hand = self.get_user_hand(user.id)
        if card_id == None:
            index = random.randrange(len(hand.cards))
            card = hand.cards.pop(index)
        else:
            filtered_cards = [card for card in hand.cards if card.id == card_id]
            if len(filtered_cards) == 0:
                raise SixQuiPrendException('Card not owned', 400)
            else:
                card = filtered_cards[0]
                hand.cards.remove(card)
        db.session.add(hand)
        chosen_card = ChosenCard(game_id=self.id, user_id=user_id, card_id=card.id)
        db.session.add(chosen_card)
        if self.chosen_cards.count() == self.users.count():
            self.is_resolving_turn = True
            db.session.add(self)
        db.session.commit()
        return chosen_card

    def choose_column_for_user(self, user_id, column_id):
        self.check_is_started()
        user = self.find_user(user_id)
        chosen_column = self.find_column(column_id)
        chosen_card = self.find_chosen_card(user_id)
        user_heap = chosen_column.replace_by_card(chosen_card)
        return [chosen_column, user_heap]

    def update_status(self):
        self.check_is_started()
        if self.chosen_cards.count() > 0:
            return
        else:
            self.is_resolving_turn = False
            db.session.add(self)
            db.session.commit()
        for user in self.users:
            if len(self.get_user_hand(user.id).cards) > 0:
                return
        self.status = Game.STATUS_FINISHED
        db.session.add(self)
        db.session.commit()

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        return {
                'id': self.id,
                'users': self.users.all(),
                'owner_id': self.owner_id,
                'status': self.status,
                }
