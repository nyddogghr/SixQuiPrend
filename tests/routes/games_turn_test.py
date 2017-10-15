from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models.card import Card
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.column import Column
from sixquiprend.models.game import Game
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import random
import unittest

class GamesTurnTestCase(unittest.TestCase):

    USERNAME = 'User'
    PASSWORD = 'Password'
    ADMIN_USERNAME = 'Admin'
    ADMIN_PASSWORD = 'Password'

    def setUp(self):
        app.config['SERVER_NAME'] = 'localhost'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DATABASE_NAME'] = 'sixquiprend_test'
        db_path = app.config['DATABASE_USER'] + ':' + app.config['DATABASE_PASSWORD']
        db_path += '@' + app.config['DATABASE_HOST'] + '/' + app.config['DATABASE_NAME']
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + db_path
        app.config['TESTING'] = True
        self.app = app.test_client()
        ctx = app.app_context()
        ctx.push()
        create_db()
        db.create_all()
        user = User(username=self.USERNAME,
                password=bcrypt.hash(self.PASSWORD),
                active=True)
        admin = User(username=self.ADMIN_USERNAME,
                password=bcrypt.hash(self.ADMIN_PASSWORD),
                active=True,
                urole=User.ADMIN_ROLE)
        db.session.add(user)
        db.session.add(admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        rv = self.app.post('/login', data=json.dumps(dict(
            username=self.USERNAME,
            password=self.PASSWORD,
        )), content_type='application/json')
        assert rv.status_code == 201

    def get_current_user(self):
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        result = json.loads(rv.data)
        if result['user'] != {}:
            return User.find(result['user']['id'])

    def create_user(self, active=True, urole=User.PLAYER_ROLE):
        username = 'User #'+str(User.query.count())
        password = 'Password'
        user = User(username=username,
                password=bcrypt.hash(password),
                active=active,
                urole=urole)
        db.session.add(user)
        db.session.commit()
        return user

    def create_game(self, status=Game.STATUS_CREATED):
        game = Game(status=status)
        db.session.add(game)
        db.session.commit()
        return game

    def create_column(self, game_id, cards=[]):
        column = Column(game_id=game_id)
        for card in cards:
            column.cards.append(card)
        db.session.add(column)
        db.session.commit()
        return column

    def create_heap(self, game_id, user_id, cards=[]):
        heap = Heap(game_id=game_id, user_id=user_id)
        for card in cards:
            heap.cards.append(card)
        db.session.add(heap)
        db.session.commit()
        return heap

    def create_hand(self, game_id, user_id, cards=[]):
        hand = Hand(game_id=game_id, user_id=user_id)
        for card in cards:
            hand.cards.append(card)
        db.session.add(hand)
        db.session.commit()
        return hand

    def create_card(self, number=random.randint(1, 1000),
            cow_value=random.randint(1, 1000)):
        card = Card(number=number, cow_value=cow_value)
        db.session.add(card)
        db.session.commit()
        return card

    def create_chosen_card(self, game_id, user_id, card_id=None):
        if card_id == None:
            card = self.create_card()
            card_id = card.id
        chosen_card = ChosenCard(game_id=game_id, user_id=user_id,
                card_id=card_id)
        db.session.add(chosen_card)
        db.session.commit()
        return chosen_card

    ################################################################################
    ## Routes
    ################################################################################

    def test_choose_card_for_game(self):
        self.login()
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        hand = self.create_hand(game_id=game.id, user_id=user.id, cards=[card])
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 201
        response_chosen_card = json.loads(rv.data)['chosen_card']
        assert response_chosen_card['game_id'] == game.id
        assert response_chosen_card['user_id'] == user.id
        assert response_chosen_card['card']['id'] == card.id

    def test_choose_card_for_bots(self):
        self.login()
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        hand = self.create_hand(game_id=game.id, user_id=user.id, cards=[card])
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 201
        response_chosen_card = json.loads(rv.data)['chosen_card']
        assert response_chosen_card['game_id'] == game.id
        assert response_chosen_card['user_id'] == user.id
        assert response_chosen_card['card']['id'] == card.id

    def test_resolve_turn(self):
        self.login()
        user = self.get_current_user()
        user2 = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        game.users.append(user2)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card(1, 1)
        card2 = self.create_card(2, 2)
        card3 = self.create_card(3, 3)
        user_hand = self.create_hand(game.id, user.id)
        user2_hand = self.create_hand(game.id, user2.id)
        user_heap = self.create_heap(game.id, user.id)
        user_chosen_card = self.create_chosen_card(game.id, user.id, card2.id)
        user2_chosen_card = self.create_chosen_card(game.id, user2.id, card3.id)
        column = self.create_column(game.id, [card])
        rv = self.app.post('/games/'+str(game.id)+'/turns/resolve')
        assert rv.status_code == 201
        response = json.loads(rv.data)
        assert response['chosen_column']['id'] == column.id
        assert response['user_heap']['user_id'] == user.id
        assert len(response['user_heap']['cards']) == 0

    def test_choose_column_for_card(self):
        self.login()
        game = self.create_game(status=Game.STATUS_STARTED)
        user = self.get_current_user()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card(1, 1)
        card2 = self.create_card(2, 2)
        user_chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        user_heap = self.create_heap(game.id, user.id)
        column = self.create_column(game.id, [card2])
        rv = self.app.post('/games/'+str(game.id)+'/columns/'+str(column.id)+'/choose')
        assert rv.status_code == 201
        response = json.loads(rv.data)
        assert len(response['chosen_column']['cards']) == 1
        assert response['chosen_column']['cards'][0]['id'] == card.id
        assert len(response['user_heap']['cards']) == 1
        assert response['user_heap']['cards'][0]['id'] == card2.id

if __name__ == '__main__':
    unittest.main()
