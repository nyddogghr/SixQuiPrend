from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models import *
from sixquiprend.routes import *
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class ModelsTestCase(unittest.TestCase):

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

class UserTestCase(ModelsTestCase):

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

class GameTestCase(ModelsTestCase):

    def test_get_results(self):
        user_one = self.create_user()
        user_two = self.create_user()
        game = self.create_game()
        game.users.append(user_one)
        game.owner_id = user_one.id
        game.users.append(user_two)
        db.session.add(game)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        user_one_heap = self.create_heap(game.id, user_one.id)
        user_one_heap.cards.append(card_one)
        user_two_heap = self.create_heap(game.id, user_two.id)
        user_two_heap.cards.append(card_two)
        user_two_heap.cards.append(card_three)
        results = game.get_results()
        assert results['User #0'] == 1
        assert results['User #1'] == 5

    def test_get_results_created_game(self):
        user_one = self.create_user()
        user_two = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED)
        game.users.append(user_one)
        game.owner_id = user_one.id
        game.users.append(user_two)
        db.session.add(game)
        results = game.get_results()
        assert results == {}

    def test_get_lowest_value_column(self):
        game = self.create_game()
        card_one = self.create_card(1, 10)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        card_five = self.create_card(5, 5)
        column_one = self.create_column(game.id)
        column_one.cards.append(card_one)
        column_two = self.create_column(game.id)
        column_two.cards.append(card_two)
        column_two.cards.append(card_five)
        column_two_bis = self.create_column(game.id)
        column_two_bis.cards.append(card_three)
        column_two_bis.cards.append(card_four)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.add(column_two_bis)
        db.session.commit()
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
        chosen_card = self.create_chosen_card(game.id, user.id,
                card_one.id)
        with self.assertRaises(NoSuitableColumnException) as e:
            game.get_suitable_column(chosen_card)
        assert e.exception.args[0] == user.id

    def test_get_suitable_column_user(self):
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
        chosen_card = self.create_chosen_card(game.id, user.id,
                card_four.id)
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_two

    def test_get_suitable_column_bot(self):
        bot = self.create_user(User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot)
        game.owner_id = bot.id
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
        bot_heap = self.create_heap(bot.id, game.id)
        chosen_card = self.create_chosen_card(game.id, bot.id,
                card_one.id)
        assert len(bot_heap.cards) == 0
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_one
        assert len(bot_heap.cards) == 1
        assert bot_heap.cards[0] == card_two

    def test_resolve_turn_auto_bot(self):
        user = self.create_user()
        bot = self.create_user(User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot)
        game.owner_id = bot.id
        game.users.append(user)
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
        bot_heap = self.create_heap(game.id, bot.id)
        bot_hand = self.create_hand(game.id, bot.id)
        user_heap = self.create_heap(game.id, user.id)
        user_hand = self.create_hand(game.id, user.id)
        bot_chosen_card = self.create_chosen_card(game.id, bot.id,
                card_one.id)
        user_chosen_card = self.create_chosen_card(game.id, user.id,
                card_four.id)
        assert len(bot_heap.cards) == 0
        [suitable_column, new_bot_heap] = game.resolve_turn()
        assert suitable_column == column_one
        assert new_bot_heap.user_id == bot.id
        assert len(new_bot_heap.cards) == 1
        assert new_bot_heap.cards[0] == card_two
        assert bot.has_chosen_card(game.id) == False

    def test_resolve_turn_user_complete_column(self):
        column_card_size = app.config['COLUMN_CARD_SIZE']
        app.config['COLUMN_CARD_SIZE'] = 1
        user = self.create_user()
        bot = self.create_user(User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot)
        game.owner_id = bot.id
        game.users.append(user)
        db.session.add(game)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id)
        column_one.cards.append(card_one)
        column_two = self.create_column(game.id)
        column_two.cards.append(card_two)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        bot_heap = self.create_heap(game.id, bot.id)
        bot_hand = self.create_hand(game.id, bot.id)
        user_heap = self.create_heap(game.id, user.id)
        user_hand = self.create_hand(game.id, user.id)
        user_chosen_card = self.create_chosen_card(game.id, user.id,
                card_three.id)
        bot_chosen_card = self.create_chosen_card(game.id, bot.id,
                card_four.id)
        assert len(user_heap.cards) == 0
        [suitable_column, new_user_heap] = game.resolve_turn()
        assert suitable_column == column_two
        assert new_user_heap.user_id == user.id
        assert len(new_user_heap.cards) == 1
        assert new_user_heap.cards[0] == card_two
        assert user.has_chosen_card(game.id) == False
        app.config['COLUMN_CARD_SIZE'] = column_card_size

    def test_setup_game(self):
        populate_db()
        user = self.create_user()
        game = self.create_game(Game.STATUS_CREATED)
        game.users.append(user)
        game.owner_id = user.id
        bots = User.query.filter(User.urole == User.BOT_ROLE).all()
        for bot in bots:
            game.users.append(bot)
        db.session.add(game)
        db.session.commit()
        game.setup_game()
        assert game.status == Game.STATUS_STARTED
        assert len(user.get_game_hand(game.id).cards) == app.config['HAND_SIZE']
        assert len(user.get_game_heap(game.id).cards) == 0

    def test_choose_cards_for_bots(self):
        game = self.create_game()
        card = self.create_card(1, 1)
        card2 = self.create_card(2, 2)
        card3 = self.create_card(3, 3)
        card4 = self.create_card(4, 4)
        user = self.create_user()
        bot1 = self.create_user(urole=User.BOT_ROLE)
        bot2 = self.create_user(urole=User.BOT_ROLE)
        user_hand = self.create_hand(game.id, user.id, [card])
        bot1_hand = self.create_hand(game.id, bot1.id, [card2])
        bot2_hand = self.create_hand(game.id, bot2.id, [card3])
        game.users.append(user)
        game.users.append(bot1)
        game.users.append(bot2)
        db.session.add(game)
        db.session.commit()
        bot2_chosen_card = self.create_chosen_card(game.id, bot2.id, card3.id)
        game.choose_cards_for_bots()
        assert user.has_chosen_card(game.id) == False
        bot1_chosen_card = bot1.get_chosen_card(game.id)
        assert bot1_chosen_card != None
        assert bot1_chosen_card.card_id == card2.id
        assert len(bot1.get_game_hand(game.id).cards) == 0
        assert bot2.get_game_hand(game.id).cards == [card3]

    def test_check_status(self):
        user = self.create_user()
        user2 = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        game.users.append(user2)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        hand = self.create_hand(game.id, user.id)
        hand2 = self.create_hand(game.id, user2.id, [card])
        game.check_status()
        assert game.status == Game.STATUS_STARTED
        hand2.cards = []
        db.session.add(hand2)
        db.session.commit()
        game.check_status()
        assert game.status == Game.STATUS_FINISHED

    def test_remove_owner(self):
        user1 = self.create_user()
        user2 = self.create_user()
        bot = self.create_user(urole=User.BOT_ROLE)
        game = self.create_game()
        game.users.append(user1)
        game.owner_id = user1.id
        game.owner_id = user1.id
        db.session.add(game)
        db.session.commit()
        with self.assertRaises(UserNotOwnerException) as e:
            game.remove_owner(user2.id)
        with self.assertRaises(CannotRemoveOwnerException) as e:
            game.remove_owner(user1.id)
        game.users.append(bot)
        db.session.add(game)
        db.session.commit()
        with self.assertRaises(CannotRemoveOwnerException) as e:
            game.remove_owner(user1.id)
        game.users.append(user2)
        db.session.add(game)
        db.session.commit()
        game.remove_owner(user1.id)
        db.session.refresh(game)
        assert game.owner_id == user2.id

class ColumnTestCase(ModelsTestCase):

    def test_replace_by_card(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        heap = self.create_heap(game.id, user.id)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        column = self.create_column(game.id)
        column.cards.append(card_two)
        column.cards.append(card_three)
        db.session.add(column)
        db.session.commit()
        chosen_card = self.create_chosen_card(game.id, user.id,
                card_one.id)
        assert user.get_game_heap(game.id).get_value() == 0
        column.replace_by_card(chosen_card)
        expected_value = card_two.cow_value + card_three.cow_value
        assert user.get_game_heap(game.id).get_value() == expected_value

    def test_get_value(self):
        column = Column()
        card_one = Card(number=1, cow_value=1)
        card_two = Card(number=2, cow_value=2)
        column.cards.append(card_one)
        column.cards.append(card_two)
        assert column.get_value() == card_one.cow_value + card_two.cow_value

class HeapTestCase(ModelsTestCase):

    def test_get_value(self):
        heap = Heap()
        card_one = Card(number=1, cow_value=1)
        card_two = Card(number=2, cow_value=2)
        heap.cards.append(card_one)
        heap.cards.append(card_two)
        assert heap.get_value() == card_one.cow_value + card_two.cow_value

if __name__ == '__main__':
    unittest.main()
