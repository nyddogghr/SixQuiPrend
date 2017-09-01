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

class UserTestCase(ModelsTestCase):

    def test_choose_card_for_game(self):
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = Card(number=1, cow_value=1)
        db.session.add(card)
        hand = Hand(game_id=game.id, user_id=user.id)
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
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_two)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        chosen_card = ChosenCard(card_id=card_one.id, user_id=user.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
        assert user.needs_to_choose_column(game.id) == True

class GameTestCase(ModelsTestCase):

    def test_get_results(self):
       user_one = User(username='toto', password='toto')
       user_two = User(username='titi', password='titi')
       db.session.add(user_one)
       db.session.add(user_two)
       game = Game(status=Game.STATUS_STARTED)
       game.users.append(user_one)
       game.users.append(user_two)
       db.session.add(game)
       card_one = Card(number=1, cow_value=1)
       db.session.add(card_one)
       card_two = Card(number=2, cow_value=2)
       db.session.add(card_two)
       card_three = Card(number=3, cow_value=3)
       db.session.add(card_three)
       db.session.commit()
       user_one_heap = Heap(user_id=user_one.id, game_id=game.id)
       user_one_heap.cards.append(card_one)
       user_two_heap = Heap(user_id=user_two.id, game_id=game.id)
       user_two_heap.cards.append(card_two)
       user_two_heap.cards.append(card_three)
       results = game.get_results()
       assert results['toto'] == 1
       assert results['titi'] == 5

    def test_get_lowest_value_column(self):
        game = Game(status=Game.STATUS_STARTED)
        db.session.add(game)
        card_one = Card(number=1, cow_value=10)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        card_five = Card(number=5, cow_value=5)
        db.session.add(card_five)
        db.session.commit()
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_one)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_two)
        column_two.cards.append(card_five)
        column_two_bis = Column(game_id=game.id)
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
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_two)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        chosen_card = ChosenCard(card_id=card_one.id, user_id=user.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
        with self.assertRaises(NoSuitableColumnException) as e:
            game.get_suitable_column(chosen_card)
        assert e.exception.value == user.id

    def test_get_suitable_column_user(self):
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_two)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        chosen_card = ChosenCard(card_id=card_four.id, user_id=user.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_two

    def test_get_suitable_column_bot(self):
        bot = User(username='titi', password='titi', urole = User.BOT_ROLE)
        db.session.add(bot)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(bot)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        bot_heap = Heap(game_id = game.id, user_id = bot.id)
        db.session.add(bot_heap)
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_two)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        chosen_card = ChosenCard(card_id=card_one.id, user_id=bot.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
        assert len(bot_heap.cards) == 0
        suitable_column = game.get_suitable_column(chosen_card)
        assert suitable_column == column_one
        assert len(bot_heap.cards) == 1
        assert bot_heap.cards[0] == card_two

    def test_resolve_turn_auto_bot(self):
        user = User(username='toto', password='toto')
        bot = User(username='titi', password='titi', urole = User.BOT_ROLE)
        db.session.add(user)
        db.session.add(bot)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(bot)
        game.users.append(user)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        bot_heap = Heap(game_id = game.id, user_id = bot.id)
        bot_hand = Hand(game_id = game.id, user_id = bot.id)
        user_heap = Heap(game_id = game.id, user_id = user.id)
        user_hand = Hand(game_id = game.id, user_id = user.id)
        db.session.add(bot_heap)
        db.session.add(bot_hand)
        db.session.add(user_heap)
        db.session.add(user_hand)
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_two)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_three)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        bot_chosen_card = ChosenCard(card_id=card_one.id, user_id=bot.id,
                game_id=game.id)
        user_chosen_card = ChosenCard(card_id=card_four.id, user_id=user.id,
                game_id=game.id)
        db.session.add(bot_chosen_card)
        db.session.add(user_chosen_card)
        db.session.commit()
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
        user = User(username='toto', password='toto')
        bot = User(username='titi', password='titi', urole = User.BOT_ROLE)
        db.session.add(user)
        db.session.add(bot)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(bot)
        game.users.append(user)
        db.session.add(game)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        card_four = Card(number=4, cow_value=4)
        db.session.add(card_four)
        db.session.commit()
        bot_heap = Heap(game_id = game.id, user_id = bot.id)
        bot_hand = Hand(game_id = game.id, user_id = bot.id)
        user_heap = Heap(game_id = game.id, user_id = user.id)
        user_hand = Hand(game_id = game.id, user_id = user.id)
        db.session.add(bot_heap)
        db.session.add(bot_hand)
        db.session.add(user_heap)
        db.session.add(user_hand)
        column_one = Column(game_id=game.id)
        column_one.cards.append(card_one)
        column_two = Column(game_id=game.id)
        column_two.cards.append(card_two)
        db.session.add(column_one)
        db.session.add(column_two)
        db.session.commit()
        user_chosen_card = ChosenCard(card_id=card_three.id, user_id=user.id,
                game_id=game.id)
        bot_chosen_card = ChosenCard(card_id=card_four.id, user_id=bot.id,
                game_id=game.id)
        db.session.add(bot_chosen_card)
        db.session.add(user_chosen_card)
        db.session.commit()
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
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
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
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        hand = Hand(game_id=game.id, user_id=user.id)
        db.session.add(hand)
        db.session.commit()
        game.check_status()
        assert game.status == Game.STATUS_FINISHED

class ColumnTestCase(ModelsTestCase):

    def test_replace_by_card(self):
        user = User(username='toto', password='toto')
        db.session.add(user)
        game = Game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        heap = Heap(user_id=user.id, game_id=game.id)
        db.session.add(heap)
        column = Column(game_id=game.id)
        card_one = Card(number=1, cow_value=1)
        db.session.add(card_one)
        card_two = Card(number=2, cow_value=2)
        db.session.add(card_two)
        card_three = Card(number=3, cow_value=3)
        db.session.add(card_three)
        column.cards.append(card_two)
        column.cards.append(card_three)
        db.session.add(column)
        db.session.commit()
        chosen_card = ChosenCard(card_id=card_one.id, user_id=user.id,
                game_id=game.id)
        db.session.add(chosen_card)
        db.session.commit()
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
