from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models import *
from sixquiprend.routes import *
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
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

    def create_user(self, urole=User.PLAYER_ROLE):
        username = 'User #'+str(User.query.count())
        password = 'Password'
        user = User(username=username,
                password=bcrypt.hash(password),
                active=True,
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

    def create_column(self, game_id):
        column = Column(game_id=game_id)
        db.session.add(column)
        db.session.commit()
        return column

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

    def test_choose_card_for_game(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card(1, 1)
        hand = self.create_hand(game.id, user.id)
        hand.cards.append(card)
        db.session.add(hand)
        db.session.commit()
        assert len(user.get_game_hand(game.id).cards) == 1
        chosen_card = user.get_chosen_card(game.id)
        assert chosen_card == None
        user.choose_card_for_game(game.id, card.id)
        assert len(user.get_game_hand(game.id).cards) == 0
        chosen_card = user.get_chosen_card(game.id)
        assert chosen_card != None
        assert chosen_card.card_id == card.id

    def test_choose_card_for_game_errors(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card(1, 1)
        hand = self.create_hand(game.id, user.id)
        assert len(user.get_game_hand(game.id).cards) == 0
        with self.assertRaises(CardNotOwnedException) as e:
            user.choose_card_for_game(game.id, card.id)

    def test_needs_to_choose_column(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id)
        column_one.cards.append(card_two)
        column_two = self.create_column(game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        assert user.needs_to_choose_column(game.id) == False
        chosen_card = self.create_chosen_card(game.id, user.id, card_one.id)
        assert user.needs_to_choose_column(game.id) == True
        db.session.delete(chosen_card)
        chosen_card = self.create_chosen_card(game.id, user.id, card_four.id)
        assert user.needs_to_choose_column(game.id) == False

    def test_login_statuses(self):
        user = self.create_user()
        assert user.is_anonymous() == False
        assert user.is_authenticated() == False
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        assert user.is_authenticated() == True

if __name__ == '__main__':
    unittest.main()
