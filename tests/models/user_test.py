from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models.card import Card
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.column import Column
from sixquiprend.models.game import Game
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import random
import unittest

class UserTestCase(unittest.TestCase):

    USERNAME = 'User'
    PASSWORD = 'Password'

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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self, urole=User.PLAYER_ROLE, active=True,
            authenticated=True):
        username = 'User #'+str(User.query.count())
        password = 'Password'
        user = User(username=username,
                password=bcrypt.hash(password),
                active=active,
                authenticated=authenticated,
                urole=urole)
        db.session.add(user)
        db.session.commit()
        return user

    def create_game(self, status=Game.STATUS_STARTED, users=[], owner_id=None):
        game = Game(status=status)
        for user in users:
            game.users.append(user)
        game.owner_id = owner_id
        db.session.add(game)
        db.session.commit()
        return game

    def create_hand(self, game_id, user_id, cards=[]):
        hand = Hand(game_id=game_id, user_id=user_id)
        for card in cards:
            hand.cards.append(card)
        db.session.add(hand)
        db.session.commit()
        return hand

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

    def create_chosen_card(self, game_id, user_id, card_id):
        chosen_card = ChosenCard(game_id=game_id,
                user_id=user_id,
                card_id=card_id)
        db.session.add(chosen_card)
        db.session.commit()
        return chosen_card

    def create_card(self, number=random.randint(1, 1000),
            cow_value=random.randint(1, 1000)):
        card = Card(number=number, cow_value=cow_value)
        db.session.add(card)
        db.session.commit()
        return card

    ################################################################################
    ## Getters
    ################################################################################

    def test_find(self):
        user = self.create_user()
        assert User.find(user.id) == user

    def test_find_errors(self):
        # User not found
        user = self.create_user()
        with self.assertRaises(SixQuiPrendException) as e:
            User.find(-1)
            assert e.code == 404

    ################################################################################
    ## Actions
    ################################################################################

    def test_delete(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card1 = self.create_card()
        card2 = self.create_card()
        card3 = self.create_card()
        card4 = self.create_card()
        column = self.create_column(game_id=game.id, cards=[card1])
        user_hand = self.create_hand(game_id=game.id, user_id=user.id, cards=[card2])
        user_heap = self.create_heap(game_id=game.id, user_id=user.id, cards=[card3])
        chosen_card = self.create_chosen_card(game_id=game.id, user_id=user.id,
                card_id=card4.id)
        User.delete(user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            User.find(user.id)
            assert e.code == 404
        assert Card.find(card1.id) == card1
        assert Game.find(game.id) == game
        assert Column.query.get(column.id) == column
        assert Hand.query.get(user_hand.id) == None
        assert Heap.query.get(user_heap.id) == None
        assert ChosenCard.query.get(chosen_card.id) == None

    def test_register(self):
        user = User.register('toto', 'titi')
        assert User.find(user.id) == user

    def test_register_errors(self):
        # Username already present
        user = self.create_user()
        with self.assertRaises(SixQuiPrendException) as e:
            User.register(user.username, 'titi')
            assert e.code == 400

    def test_login(self):
        user = User.register('toto', 'titi')
        assert User.login('toto', 'titi') == user

    def test_login_errors(self):
        # User is a bot
        user = self.create_user(urole=User.ROLE_BOT)
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'Password')
            assert e.code == 403
        # User is not active
        user = self.create_user(active=False)
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'Password')
            assert e.code == 403
        # Password is invalid
        user = self.create_user()
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'NotPassword')
            assert e.code == 400

    def test_logout(self):
        user = self.create_user(authenticated=True)
        assert user.is_authenticated() == True
        user.logout()
        assert user.is_authenticated() == False

    def test_change_active(self):
        user = self.create_user(active=True)
        assert user.is_active() == True
        user.change_active(False)
        assert user.is_active() == False
        user.change_active(True)
        assert user.is_active() == True

if __name__ == '__main__':
    unittest.main()
