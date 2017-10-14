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
import json
import random
import unittest

class GameTestCase(unittest.TestCase):

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

    def create_game(self, status=Game.STATUS_STARTED, users=[]):
        game = Game(status=status)
        for user in users:
            game.users.append(user)
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
        game = self.create_game()
        assert Game.find(game.id) == game

    def test_find_errors(self):
        with self.assertRaises(SixQuiPrendException) as e:
            Game.find(-1)
            assert e.code == 404

    def test_find_user(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        assert game.find_user(user.id) == user

    def test_find_user_errors(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        with self.assertRaises(SixQuiPrendException) as e:
            game.find_user(-1)
            assert e.code == 404

    def test_get_find_column(self):
        game = self.create_game()
        column = self.create_column(game.id)
        assert game.find_column(column.id)

    def test_get_find_column_errors(self):
        game = self.create_game()
        column = self.create_column(game.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.find_column(-1)
            assert e.code == 404

    def test_get_user_status(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        assert game.get_user_status(user.id)['has_chosen_card'] == False
        assert game.get_user_status(user.id)['needs_to_choose_column'] == False

    def test_check_is_owner(self):
        user = self.create_user()
        game = self.create_game()
        game.owner_id = user.id
        game.check_is_owner(user.id)

    def test_check_is_owner_errors(self):
        user = self.create_user()
        game = self.create_game()
        with self.assertRaises(SixQuiPrendException) as e:
            game.check_is_owner(user.id)
            assert e.code == 403

    def test_get_results(self):
        user_one = self.create_user()
        user_two = self.create_user()
        game = self.create_game(users=[user_one, user_two])
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        user_one_heap = self.create_heap(game.id, user_one.id)
        user_one_heap.cards.append(card_one)
        user_two_heap = self.create_heap(game.id, user_two.id)
        user_two_heap.cards.append(card_two)
        user_two_heap.cards.append(card_three)
        results = game.get_results()
        assert results[user_one.username] == 1
        assert results[user_two.username] == 5

    def test_get_results_created_game(self):
        user_one = self.create_user()
        user_two = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED, users=[user_one,
            user_two])
        results = game.get_results()
        assert results == {}

    def test_get_lowest_value_column(self):
        game = self.create_game()
        card_one = self.create_card(1, 10)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        card_five = self.create_card(5, 5)
        column_one = self.create_column(game.id, cards=[card_one])
        column_two = self.create_column(game.id, cards=[card_two, card_five])
        column_two_bis = self.create_column(game.id, cards=[card_three,
            card_four])
        assert column_one.get_value() > column_two.get_value()
        assert column_two.get_value() == column_two_bis.get_value()
        chosen_column_ids = []
        for i in range(100):
            chosen_column = game.get_lowest_value_column()
            assert chosen_column.id != column_one.id
            chosen_column_ids.append(chosen_column.id)
        assert chosen_column_ids.index(column_two.id) >= 0
        assert chosen_column_ids.index(column_two_bis.id) >= 0

    def test_get_suitable_column_exception(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        chosen_card = self.create_chosen_card(game.id, user.id,
                card_one.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.get_suitable_column(chosen_card)
            assert e.code == 422

    def test_get_suitable_column_user(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        chosen_card = self.create_chosen_card(game.id, user.id,
                card_four.id)
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_two

    def test_user_needs_to_choose_column(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        assert game.user_needs_to_choose_column(user.id) == False
        chosen_card = self.create_chosen_card(game.id, user.id, card_one.id)
        assert game.user_needs_to_choose_column(user.id) == True
        db.session.delete(chosen_card)
        chosen_card = self.create_chosen_card(game.id, user.id, card_four.id)
        assert game.user_needs_to_choose_column(user.id) == False

    ################################################################################
    ## Actions
    ################################################################################

    # def test_setup_game(self):
        # populate_db()
        # user = self.create_user()
        # game = self.create_game(Game.STATUS_CREATED)
        # game.users.append(user)
        # game.owner_id = user.id
        # bots = User.query.filter(User.urole == User.BOT_ROLE).all()
        # for bot in bots:
            # game.users.append(bot)
        # db.session.add(game)
        # db.session.commit()
        # game.setup_game()
        # assert game.status == Game.STATUS_STARTED
        # assert len(user.get_game_hand(game.id).cards) == app.config['HAND_SIZE']
        # assert len(user.get_game_heap(game.id).cards) == 0

    # def test_remove_owner(self):
        # user1 = self.create_user()
        # user2 = self.create_user()
        # bot = self.create_user(urole=User.BOT_ROLE)
        # game = self.create_game()
        # game.users.append(user1)
        # game.owner_id = user1.id
        # game.owner_id = user1.id
        # db.session.add(game)
        # db.session.commit()
        # with self.assertRaises(UserNotOwnerException) as e:
            # game.remove_owner(user2.id)
        # with self.assertRaises(CannotRemoveOwnerException) as e:
            # game.remove_owner(user1.id)
        # game.users.append(bot)

    # def test_resolve_turn_auto_bot(self):
        # user = self.create_user()
        # bot = self.create_user(User.BOT_ROLE)
        # game = self.create_game()
        # game.users.append(bot)
        # game.owner_id = bot.id
        # game.users.append(user)
        # db.session.add(game)
        # card_one = self.create_card(1, 1)
        # card_two = self.create_card(2, 2)
        # card_three = self.create_card(3, 3)
        # card_four = self.create_card(4, 4)
        # column_one = self.create_column(game.id)
        # column_one.cards.append(card_two)
        # column_two = self.create_column(game.id)
        # column_two.cards.append(card_three)
        # db.session.add(column_one)
        # db.session.add(column_two)
        # db.session.commit()
        # bot_heap = self.create_heap(game.id, bot.id)
        # bot_hand = self.create_hand(game.id, bot.id)
        # user_heap = self.create_heap(game.id, user.id)
        # user_hand = self.create_hand(game.id, user.id)
        # bot_chosen_card = self.create_chosen_card(game.id, bot.id,
                # card_one.id)
        # user_chosen_card = self.create_chosen_card(game.id, user.id,
                # card_four.id)
        # assert len(bot_heap.cards) == 0
        # [suitable_column, new_bot_heap] = game.resolve_turn()
        # assert suitable_column == column_one
        # assert new_bot_heap.user_id == bot.id
        # assert len(new_bot_heap.cards) == 1
        # assert new_bot_heap.cards[0] == card_two
        # assert bot.has_chosen_card(game.id) == False

    # def test_resolve_turn_error_user(self):
        # user = self.create_user()
        # user2 = self.create_user()
        # game = self.create_game()
        # game.users.append(user2)
        # game.owner_id = user2.id
        # game.users.append(user)
        # db.session.add(game)
        # card_one = self.create_card(1, 1)
        # card_two = self.create_card(2, 2)
        # card_three = self.create_card(3, 3)
        # card_four = self.create_card(4, 4)
        # column_one = self.create_column(game.id)
        # column_one.cards.append(card_two)
        # column_two = self.create_column(game.id)
        # column_two.cards.append(card_three)
        # db.session.add(column_one)
        # db.session.add(column_two)
        # db.session.commit()
        # user2_heap = self.create_heap(game.id, user2.id)
        # user2_hand = self.create_hand(game.id, user2.id)
        # user_heap = self.create_heap(game.id, user.id)
        # user_hand = self.create_hand(game.id, user.id)
        # user2_chosen_card = self.create_chosen_card(game.id, user2.id,
                # card_one.id)
        # user_chosen_card = self.create_chosen_card(game.id, user.id,
                # card_four.id)
        # assert len(user2_heap.cards) == 0
        # with self.assertRaises(NoSuitableColumnException) as e:
            # [suitable_column, new_user2_heap] = game.resolve_turn()
        # assert e.exception.args[0] == user2.id

    # def test_resolve_turn_user_complete_column(self):
        # column_card_size = app.config['COLUMN_CARD_SIZE']
        # app.config['COLUMN_CARD_SIZE'] = 1
        # user = self.create_user()
        # bot = self.create_user(User.BOT_ROLE)
        # game = self.create_game()
        # game.users.append(bot)
        # game.owner_id = bot.id
        # game.users.append(user)
        # db.session.add(game)
        # card_one = self.create_card(1, 1)
        # card_two = self.create_card(2, 2)
        # card_three = self.create_card(3, 3)
        # card_four = self.create_card(4, 4)
        # column_one = self.create_column(game.id)
        # column_one.cards.append(card_one)
        # column_two = self.create_column(game.id)
        # column_two.cards.append(card_two)
        # db.session.add(column_one)
        # db.session.add(column_two)
        # db.session.commit()
        # bot_heap = self.create_heap(game.id, bot.id)
        # bot_hand = self.create_hand(game.id, bot.id)
        # user_heap = self.create_heap(game.id, user.id)
        # user_hand = self.create_hand(game.id, user.id)
        # user_chosen_card = self.create_chosen_card(game.id, user.id,
                # card_three.id)
        # bot_chosen_card = self.create_chosen_card(game.id, bot.id,
                # card_four.id)
        # assert len(user_heap.cards) == 0
        # [suitable_column, new_user_heap] = game.resolve_turn()
        # assert suitable_column == column_two
        # assert new_user_heap.user_id == user.id
        # assert len(new_user_heap.cards) == 1
        # assert new_user_heap.cards[0] == card_two
        # assert user.has_chosen_card(game.id) == False
        # app.config['COLUMN_CARD_SIZE'] = column_card_size

    # def test_choose_cards_for_bots(self):
        # game = self.create_game()
        # card = self.create_card(1, 1)
        # card2 = self.create_card(2, 2)
        # card3 = self.create_card(3, 3)
        # card4 = self.create_card(4, 4)
        # user = self.create_user()
        # bot1 = self.create_user(urole=User.BOT_ROLE)
        # bot2 = self.create_user(urole=User.BOT_ROLE)
        # user_hand = self.create_hand(game.id, user.id, [card])
        # bot1_hand = self.create_hand(game.id, bot1.id, [card2])
        # bot2_hand = self.create_hand(game.id, bot2.id, [card3])
        # game.users.append(user)
        # game.users.append(bot1)
        # game.users.append(bot2)
        # db.session.add(game)
        # db.session.commit()
        # bot2_chosen_card = self.create_chosen_card(game.id, bot2.id, card3.id)
        # game.choose_cards_for_bots()
        # assert user.has_chosen_card(game.id) == False
        # bot1_chosen_card = bot1.get_chosen_card(game.id)
        # assert bot1_chosen_card != None
        # assert bot1_chosen_card.card_id == card2.id
        # assert len(bot1.get_game_hand(game.id).cards) == 0
        # assert bot2.get_game_hand(game.id).cards == [card3]

    # def test_update_status(self):
        # user = self.create_user()
        # user2 = self.create_user()
        # game = self.create_game(status=Game.STATUS_STARTED)
        # game.users.append(user)
        # game.users.append(user2)
        # game.owner_id = user.id
        # db.session.add(game)
        # db.session.commit()
        # card = self.create_card()
        # hand = self.create_hand(game.id, user.id)
        # hand2 = self.create_hand(game.id, user2.id, [card])
        # game.check_status()
        # assert game.status == Game.STATUS_STARTED
        # hand2.cards = []
        # db.session.add(hand2)
        # db.session.commit()
        # game.check_status()
        # assert game.status == Game.STATUS_FINISHED
        # db.session.add(game)
        # db.session.commit()
        # with self.assertRaises(CannotRemoveOwnerException) as e:
            # game.remove_owner(user1.id)
        # game.users.append(user2)
        # db.session.add(game)
        # db.session.commit()
        # game.remove_owner(user1.id)
        # db.session.refresh(game)
        # assert game.owner_id == user2.id

    # def test_choose_card_for_user(self):
        # user = self.create_user()
        # game = self.create_game()
        # game.users.append(user)
        # game.owner_id = user.id
        # db.session.add(game)
        # db.session.commit()
        # card = self.create_card(1, 1)
        # hand = self.create_hand(game.id, user.id)
        # hand.cards.append(card)
        # db.session.add(hand)
        # db.session.commit()
        # assert len(user.get_game_hand(game.id).cards) == 1
        # chosen_card = user.get_chosen_card(game.id)
        # assert chosen_card == None
        # user.choose_card_for_game(game.id, card.id)
        # assert len(user.get_game_hand(game.id).cards) == 0
        # chosen_card = user.get_chosen_card(game.id)
        # assert chosen_card != None
        # assert chosen_card.card_id == card.id

    # def test_choose_card_for_user_errors(self):
        # user = self.create_user()
        # game = self.create_game()
        # game.users.append(user)
        # game.owner_id = user.id
        # db.session.add(game)
        # db.session.commit()
        # card = self.create_card(1, 1)
        # hand = self.create_hand(game.id, user.id)
        # assert len(user.get_game_hand(game.id).cards) == 0
        # with self.assertRaises(CardNotOwnedException) as e:
            # user.choose_card_for_game(game.id, card.id)

if __name__ == '__main__':
    unittest.main()
