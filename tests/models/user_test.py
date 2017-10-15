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

    def create_game(self, status=Game.STATUS_STARTED):
        game = Game(status=status)
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

    def create_heap(self, game_id, user_id):
        heap = Heap(game_id=game_id, user_id=user_id)
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

    def test_get_game_heap(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        heap = self.create_heap(game.id, user.id)
        assert user.get_game_heap(game.id) == heap

    def test_get_game_hand(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        hand = self.create_hand(game.id, user.id)
        assert user.get_game_hand(game.id) == hand

    def test_has_chosen_card(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        assert user.has_chosen_card(game.id) == False
        chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        assert user.has_chosen_card(game.id) == True

    def test_get_chosen_card(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        assert user.get_chosen_card(game.id) == chosen_card

    ################################################################################
    ## Actions
    ################################################################################

    def test_delete(self):
        user = self.create_user()
        User.delete(user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            User.find(user.id)
            assert e.code == 404

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
        user = self.create_user(urole = User.BOT_ROLE)
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'Password')
            assert e.code == 403
        # User is not active
        user = self.create_user(active = False)
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'Password')
            assert e.code == 403
        # Password is invalid is not active
        user = self.create_user()
        with self.assertRaises(SixQuiPrendException) as e:
            User.login(user.username, 'NotPassword')
            assert e.code == 400

    def test_logout(self):
        user = self.create_user(authenticated = True)
        assert user.is_authenticated() == True
        user.logout()
        assert user.is_authenticated() == False

    def test_change_active(self):
        user = self.create_user(active = True)
        assert user.is_active() == True
        user.change_active(False)
        assert user.is_active() == False
        user.change_active(True)
        assert user.is_active() == True

if __name__ == '__main__':
    unittest.main()
