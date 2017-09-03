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
                password = bcrypt.hash(password),
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

    def create_hand(self, user_id, game_id):
        hand = Hand(user_id=user_id, game_id=game_id)
        db.session.add(hand)
        db.session.commit()
        return hand

    def create_column(self, game_id):
        column = Column(game_id=game_id)
        db.session.add(column)
        db.session.commit()
        return column

    def create_heap(self, user_id, game_id):
        heap = Heap(user_id=user_id, game_id=game_id)
        db.session.add(heap)
        db.session.commit()
        return heap

    def create_chosen_card(self, card_id, user_id, game_id):
        chosen_card = ChosenCard(card_id=card_id,
                user_id=user_id,
                game_id=game_id)
        db.session.add(chosen_card)
        db.session.commit()
        return chosen_card

    def create_card(self, number, cow_value):
        card = Card(number=number, cow_value=cow_value)
        db.session.add(card)
        db.session.commit()
        return card

class UserTestCase(ModelsTestCase):

    def test_choose_card_for_game(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card(1, 1)
        hand = self.create_hand(user.id, game.id)
        hand.cards.append(card)
        db.session.add(hand)
        db.session.commit()
        assert len(user.get_game_hand(game.id).cards) == 1
        chosen_card = ChosenCard.query.filter(ChosenCard.game_id == game.id,
                ChosenCard.user_id == user.id,
                ChosenCard.card_id == card.id).first()
        assert chosen_card == None
        user.choose_card_for_game(game.id, card.id)
        assert len(user.get_game_hand(game.id).cards) == 0
        chosen_card = ChosenCard.query.filter(ChosenCard.game_id == game.id,
                ChosenCard.user_id == user.id,
                ChosenCard.card_id == card.id).first()
        assert chosen_card != None

    def test_needs_to_choose_column(self):
        user = self.create_user()
        game = self.create_game()
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
        assert user.needs_to_choose_column(game.id) == False
        chosen_card = ChosenCard(card_id=card_one.id, user_id=user.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
        assert user.needs_to_choose_column(game.id) == True

class GameTestCase(ModelsTestCase):

    def test_get_results(self):
       user_one = self.create_user()
       user_two = self.create_user()
       game = self.create_game()
       game.users.append(user_one)
       game.users.append(user_two)
       db.session.add(game)
       card_one = self.create_card(1, 1)
       card_two = self.create_card(2, 2)
       card_three = self.create_card(3, 3)
       user_one_heap = self.create_heap(user_one.id, game.id)
       user_one_heap.cards.append(card_one)
       user_two_heap = self.create_heap(user_two.id, game.id)
       user_two_heap.cards.append(card_two)
       user_two_heap.cards.append(card_three)
       results = game.get_results()
       assert results['User #0'] == 1
       assert results['User #1'] == 5

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
        chosen_card = self.create_chosen_card(card_one.id,
                user.id,
                game.id)
        with self.assertRaises(NoSuitableColumnException) as e:
            game.get_suitable_column(chosen_card)
        assert e.exception.value == user.id

    def test_get_suitable_column_user(self):
        user = self.create_user()
        game = self.create_game()
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
        chosen_card = self.create_chosen_card(card_four.id,
                user.id,
                game.id)
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_two

    def test_get_suitable_column_bot(self):
        bot = self.create_user(User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot)
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
        chosen_card = self.create_chosen_card(card_one.id,
                bot.id,
                game.id)
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
        bot_heap = self.create_heap(bot.id, game.id)
        bot_hand = self.create_hand(bot.id, game.id)
        user_heap = self.create_heap(user.id, game.id)
        user_hand = self.create_hand(user.id, game.id)
        bot_chosen_card = self.create_chosen_card(card_one.id,
                bot.id,
                game.id)
        user_chosen_card = self.create_chosen_card(card_four.id,
                user.id,
                game.id)
        assert len(bot_heap.cards) == 0
        [suitable_column, new_bot_heap] = game.resolve_turn()
        assert suitable_column == column_one
        assert new_bot_heap.user_id == bot.id
        assert len(new_bot_heap.cards) == 1
        assert new_bot_heap.cards[0] == card_two
        bot_chosen_card = ChosenCard.query.filter(ChosenCard.user_id == bot.id).first()
        assert bot_chosen_card == None

    def test_resolve_turn_user_complete_column(self):
        app.config['COLUMN_CARD_SIZE'] = 1
        user = self.create_user()
        bot = self.create_user(User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot)
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
        bot_heap = self.create_heap(bot.id, game.id)
        bot_hand = self.create_hand(bot.id, game.id)
        user_heap = self.create_heap(user.id, game.id)
        user_hand = self.create_hand(user.id, game.id)
        user_chosen_card = self.create_chosen_card(card_three.id,
                user.id,
                game.id)
        bot_chosen_card = self.create_chosen_card(card_four.id,
                bot.id,
                game.id)
        assert len(user_heap.cards) == 0
        [suitable_column, new_user_heap] = game.resolve_turn()
        assert suitable_column == column_two
        assert new_user_heap.user_id == user.id
        assert len(new_user_heap.cards) == 1
        assert new_user_heap.cards[0] == card_two
        user_chosen_card = ChosenCard.query.filter(ChosenCard.user_id == user.id).first()
        assert user_chosen_card == None

    def test_setup_game(self):
        populate_db()
        user = self.create_user()
        game = self.create_game(Game.STATUS_CREATED)
        game.users.append(user)
        bots = User.query.filter(User.urole == User.BOT_ROLE).all()
        for bot in bots:
            game.users.append(bot)
        db.session.add(game)
        db.session.commit()
        game.setup_game()
        assert game.status == Game.STATUS_STARTED
        assert len(user.get_game_hand(game.id).cards) == app.config['HAND_SIZE']
        assert len(user.get_game_heap(game.id).cards) == 0

    def test_check_status(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        hand = self.create_hand(user.id, game.id)
        game.check_status()
        assert game.status == Game.STATUS_FINISHED

class ColumnTestCase(ModelsTestCase):

    def test_replace_by_card(self):
        user = self.create_user()
        game = self.create_game()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        heap = self.create_heap(user.id, game.id)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        column = self.create_column(game.id)
        column.cards.append(card_two)
        column.cards.append(card_three)
        db.session.add(column)
        db.session.commit()
        chosen_card = self.create_chosen_card(card_one.id,
                user.id,
                game.id)
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
