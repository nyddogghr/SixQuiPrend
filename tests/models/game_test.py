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

    def create_chosen_card(self, game_id, user_id, card_id=None):
        if card_id == None:
            card_id = self.create_card().id
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
        # Game not found
        with self.assertRaises(SixQuiPrendException) as e:
            Game.find(-1)
            assert e.code == 404

    def test_find_user(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        assert game.find_user(user.id) == user

    def test_find_user_errors(self):
        # User not in game
        user = self.create_user()
        game = self.create_game(users=[user])
        with self.assertRaises(SixQuiPrendException) as e:
            game.find_user(-1)
            assert e.code == 404

    def test_find_column(self):
        game = self.create_game()
        column = self.create_column(game.id)
        assert game.find_column(column.id)

    def test_find_column_errors(self):
        # Column not in game
        game = self.create_game()
        column = self.create_column(game.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.find_column(-1)
            assert e.code == 404

    def test_find_chosen_card(self):
        user = self.create_user()
        game = self.create_game()
        chosen_card = self.create_chosen_card(game.id, user.id)
        assert game.find_chosen_card(chosen_card.id)

    def test_find_chosen_card_errors(self):
        # Chosen card not in game
        user = self.create_user()
        game = self.create_game()
        chosen_card = self.create_chosen_card(game.id, user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.find_chosen_card(-1)
            assert e.code == 404

    def test_get_user_status(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        assert game.get_user_status(user.id)['has_chosen_card'] == False
        assert game.get_user_status(user.id)['needs_to_choose_column'] == False

    def test_get_user_chosen_card(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card = self.create_card()
        chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        assert game.get_user_chosen_card(user.id) == chosen_card

    def test_check_is_started(self):
        game = self.create_game(status=Game.STATUS_STARTED)
        game.check_is_started()

    def test_check_is_started_errors(self):
        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        with self.assertRaises(SixQuiPrendException) as e:
            game.check_is_started()
            assert e.code == 400

    def test_check_is_owner(self):
        user = self.create_user()
        game = self.create_game(owner_id=user.id)
        game.check_is_owner(user.id)

    def test_check_is_owner_errors(self):
        # User not owner
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

    def test_get_suitable_column(self):
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

    def test_get_suitable_column_errors(self):
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

    def test_get_available_bots(self):
        bot1 = self.create_user(urole=User.ROLE_BOT)
        bot2 = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(users=[bot1])
        assert game.get_available_bots() == [bot2]

    def test_get_chosen_cards_for_current_user(self):
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2])
        chosen_card1 = self.create_chosen_card(game.id, user1.id)
        chosen_cards = game.get_chosen_cards_for_current_user(user1.id)
        assert chosen_cards == [chosen_card1]
        chosen_card2 = self.create_chosen_card(game.id, user2.id)
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        chosen_cards = game.get_chosen_cards_for_current_user(user1.id)
        assert chosen_cards == [chosen_card1, chosen_card2]
        db.session.delete(chosen_card1)
        db.session.refresh(game)
        chosen_cards = game.get_chosen_cards_for_current_user(user1.id)
        assert chosen_cards == [chosen_card2]

    def test_get_chosen_cards_for_current_user_errors(self):
        # User has no chosen card and card is not being placed
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2])
        with self.assertRaises(SixQuiPrendException) as e:
            game.get_chosen_cards_for_current_user(user1.id)
            assert e.code == 400

    def test_user_needs_to_choose_column(self):
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2])
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        card_five = self.create_card(5, 5)
        column_one = self.create_column(game.id, cards=[card_three])
        column_two = self.create_column(game.id, cards=[card_four])
        assert game.user_needs_to_choose_column(user1.id) == False
        assert game.user_needs_to_choose_column(user2.id) == False
        chosen_card1 = self.create_chosen_card(game.id, user1.id, card_two.id)
        assert game.user_needs_to_choose_column(user1.id) == True
        assert game.user_needs_to_choose_column(user2.id) == False
        chosen_card2 = self.create_chosen_card(game.id, user2.id, card_one.id)
        assert game.user_needs_to_choose_column(user1.id) == False
        assert game.user_needs_to_choose_column(user2.id) == True
        db.session.delete(chosen_card2)
        chosen_card2 = self.create_chosen_card(game.id, user2.id, card_five.id)
        assert game.user_needs_to_choose_column(user1.id) == True
        assert game.user_needs_to_choose_column(user2.id) == False

    def test_can_place_card(self):
        user1 = self.create_user()
        user2 = self.create_user()
        bot = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(users=[user1, user2, bot], owner_id=user1.id)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        card_five = self.create_card(5, 5)
        card_six = self.create_card(6, 6)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        assert game.can_place_card(user1.id) == False
        chosen_card1 = self.create_chosen_card(game.id, user1.id, card_four.id)
        assert game.can_place_card(user1.id) == False
        chosen_cardb = self.create_chosen_card(game.id, bot.id, card_five.id)
        chosen_card2 = self.create_chosen_card(game.id, user2.id, card_six.id)
        assert game.can_place_card(user1.id) == True
        db.session.delete(chosen_card1)
        assert game.can_place_card(user1.id) == False
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        assert game.can_place_card(user1.id) == True
        chosen_card1 = self.create_chosen_card(game.id, user1.id, card_one.id)
        assert game.can_place_card(user1.id) == False
        db.session.delete(chosen_card1)
        db.session.delete(chosen_cardb)
        chosen_cardb = self.create_chosen_card(game.id, bot.id, card_one.id)
        assert game.can_place_card(user1.id) == True

    def test_can_choose_cards_for_bots(self):
        user = self.create_user()
        bot1 = self.create_user(urole=User.ROLE_BOT)
        bot2 = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(users=[user, bot1, bot2], owner_id=user.id)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        column_one = self.create_column(game.id, cards=[card_one])
        assert game.can_choose_cards_for_bots(user.id) == True
        chosen_card1 = self.create_chosen_card(game.id, bot1.id, card_one.id)
        assert game.can_choose_cards_for_bots(user.id) == True
        chosen_card2 = self.create_chosen_card(game.id, bot2.id, card_two.id)
        assert game.can_choose_cards_for_bots(user.id) == False
        db.session.delete(chosen_card1)
        assert game.can_choose_cards_for_bots(user.id) == True
        chosen_card2 = self.create_chosen_card(game.id, user.id, card_two.id)
        assert game.can_choose_cards_for_bots(user.id) == True
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        assert game.can_choose_cards_for_bots(user.id) == False

    ################################################################################
    ## Actions
    ################################################################################

    def test_create(self):
        user = self.create_user()
        game = Game.create(user)
        assert game.users.all() == [user]
        assert game.owner_id == user.id
        assert game.status == Game.STATUS_CREATED

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
        Game.delete(game.id)
        assert Card.find(card1.id) == card1
        assert User.find(user.id) == user
        assert Column.query.get(column.id) == None
        assert Hand.query.get(user_hand.id) == None
        assert Heap.query.get(user_heap.id) == None
        with self.assertRaises(SixQuiPrendException) as e:
            Game.find(game.id)
            assert e.code == 404
        assert ChosenCard.query.get(chosen_card.id) == None

    def test_setup_game(self):
        populate_db()
        user = self.create_user()
        users = [user]
        bots = User.query.filter(User.urole == User.ROLE_BOT).all()
        for bot in bots:
            users.append(bot)
        game = self.create_game(Game.STATUS_CREATED, users=users, owner_id=user.id)
        game.setup(user.id)
        assert game.status == Game.STATUS_STARTED
        assert game.columns.count() == app.config['BOARD_SIZE']
        for column in game.columns:
            assert len(column.cards) == 1
        assert len(game.get_user_hand(user.id).cards) == app.config['HAND_SIZE']
        assert len(game.get_user_heap(user.id).cards) == 0

    def test_setup_game_errors(self):
        # User is not owner
        user = self.create_user()
        game = self.create_game(Game.STATUS_CREATED, users=[user])
        with self.assertRaises(SixQuiPrendException) as e:
            game.setup(user.id)
            assert e.code == 400
        # Game is not CREATED
        user = self.create_user()
        game = self.create_game(Game.STATUS_STARTED, users=[user], owner_id=user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.setup(user.id)
            assert e.code == 400
        # Not enough users
        game = self.create_game(Game.STATUS_CREATED, users=[user], owner_id=user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.setup(user.id)
            assert e.code == 400

    def test_add_user(self):
        user = self.create_user()
        game = self.create_game(Game.STATUS_CREATED)
        assert game.users.count() == 0
        game.add_user(user)
        assert game.users.all() == [user]

    def test_add_user_errors(self):
        # Game not CREATED
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        with self.assertRaises(SixQuiPrendException) as e:
            game.add_user(user)
            assert e.code == 400
        # Max number of users reached
        game = self.create_game(Game.STATUS_CREATED)
        for i in range(app.config['MAX_PLAYER_NUMBER']):
            game.add_user(self.create_user())
        with self.assertRaises(SixQuiPrendException) as e:
            game.add_user(user)
            assert e.code == 400
        # Already in game
        game = self.create_game(Game.STATUS_CREATED, users=[user])
        with self.assertRaises(SixQuiPrendException) as e:
            game.add_user(user)
            assert e.code == 400

    def test_add_bot(self):
        bot = self.create_user(urole=User.ROLE_BOT)
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED, owner_id=user.id)
        assert game.users.count() == 0
        game.add_bot(bot.id, user.id)
        assert game.users.all() == [bot]

    def test_add_bot_errors(self):
        # User not a bot
        not_bot = self.create_user(urole=User.PLAYER_ROLE)
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED, owner_id=user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.add_bot(not_bot.id, user.id)
            assert e.code == 400

    def test_remove_user(self):
        user = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user, user2])
        card1 = self.create_card()
        card2 = self.create_card()
        card3 = self.create_card()
        card4 = self.create_card()
        column = self.create_column(game_id=game.id, cards=[card1])
        user_hand = self.create_hand(game_id=game.id, user_id=user.id, cards=[card2])
        user_heap = self.create_heap(game_id=game.id, user_id=user.id, cards=[card3])
        chosen_card = self.create_chosen_card(game_id=game.id, user_id=user.id,
                card_id=card4.id)
        assert game.users.count() == 2
        game.remove_user(user)
        assert game.users.all() == [user2]
        assert Card.find(card1.id) == card1
        assert User.find(user.id) == user
        assert Column.query.get(column.id) == column
        assert Hand.query.get(user_hand.id) == None
        assert Heap.query.get(user_heap.id) == None
        assert ChosenCard.query.get(chosen_card.id) == None

    def test_remove_user_errors(self):
        # User not in game
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1])
        with self.assertRaises(SixQuiPrendException) as e:
            game.remove_user(user2)
            assert e.code == 400

    def test_remove_owner(self):
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2], owner_id=user1.id)
        game.remove_owner(user1.id)
        assert game.owner_id == user2.id

    def test_remove_owner_errors(self):
        # User not owner
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2], owner_id=user1.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.remove_owner(user2.id)
            assert e.code == 400
        # No other non bot player
        user = self.create_user()
        bot = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(users=[user, bot], owner_id=user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.remove_owner(user.id)
            assert e.code == 400

    def test_place_card(self):
        column_card_size = app.config['COLUMN_CARD_SIZE']
        app.config['COLUMN_CARD_SIZE'] = 2
        user = self.create_user()
        bot = self.create_user(User.ROLE_BOT)
        game = self.create_game(users=[user, bot], owner_id=user.id)
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        card_five = self.create_card(5, 5)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three, card_four])
        bot_heap = self.create_heap(game.id, bot.id)
        bot_hand = self.create_hand(game.id, bot.id)
        user_heap = self.create_heap(game.id, user.id)
        user_hand = self.create_hand(game.id, user.id)
        bot_chosen_card = self.create_chosen_card(game.id, bot.id,
                card_one.id)
        user_chosen_card = self.create_chosen_card(game.id, user.id,
                card_five.id)
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        # Bot auto placing
        assert len(bot_heap.cards) == 0
        [suitable_column, new_bot_heap] = game.place_card(user.id)
        assert suitable_column == column_one
        assert new_bot_heap.user_id == bot.id
        assert len(new_bot_heap.cards) == 1
        assert new_bot_heap.cards[0] == card_two
        assert game.get_user_chosen_card(bot.id) == None
        assert game.can_place_card(user.id) == True
        assert game.is_resolving_turn == True
        # User completes a column
        assert len(user_heap.cards) == 0
        [suitable_column, new_user_heap] = game.place_card(user.id)
        assert suitable_column == column_two
        assert new_user_heap.user_id == user.id
        assert len(new_user_heap.cards) == 2
        assert new_user_heap.cards == [card_three, card_four]
        assert game.get_user_chosen_card(user.id) == None
        assert game.can_place_card(user.id) == False
        assert game.is_resolving_turn == False
        assert game.status == Game.STATUS_FINISHED
        app.config['COLUMN_CARD_SIZE'] = column_card_size

    def test_place_card_errors(self):
        # No chosen card to place
        user1 = self.create_user()
        user2 = self.create_user()
        game = self.create_game(users=[user1, user2], owner_id=user1.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.place_card(user1.id)
            assert e.code == 422
        # Not all users have chosen cards
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        user2_heap = self.create_heap(game.id, user2.id)
        user2_hand = self.create_hand(game.id, user2.id)
        user1_heap = self.create_heap(game.id, user1.id)
        user1_hand = self.create_hand(game.id, user1.id)
        user2_chosen_card = self.create_chosen_card(game.id, user2.id,
                card_one.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.place_card(user1.id)
            assert e.code == 422
        # No suitable column
        card_one = self.create_card(1, 1)
        card_two = self.create_card(2, 2)
        card_three = self.create_card(3, 3)
        card_four = self.create_card(4, 4)
        column_one = self.create_column(game.id, cards=[card_two])
        column_two = self.create_column(game.id, cards=[card_three])
        user2_heap = self.create_heap(game.id, user2.id)
        user2_hand = self.create_hand(game.id, user2.id)
        user1_heap = self.create_heap(game.id, user1.id)
        user1_hand = self.create_hand(game.id, user1.id)
        user2_chosen_card = self.create_chosen_card(game.id, user2.id,
                card_one.id)
        user1_chosen_card = self.create_chosen_card(game.id, user1.id,
                card_four.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.place_card(user1.id)
            assert e.code == 422

    def test_choose_cards_for_bots(self):
        card = self.create_card(1, 1)
        card2 = self.create_card(2, 2)
        card3 = self.create_card(3, 3)
        card4 = self.create_card(4, 4)
        user = self.create_user()
        bot1 = self.create_user(urole=User.ROLE_BOT)
        bot2 = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(users=[user, bot1, bot2], owner_id=user.id)
        user_hand = self.create_hand(game.id, user.id, [card])
        bot1_hand = self.create_hand(game.id, bot1.id, [card2])
        bot2_hand = self.create_hand(game.id, bot2.id, [card3])
        bot2_chosen_card = self.create_chosen_card(game.id, bot2.id, card3.id)
        game.choose_cards_for_bots(user.id)
        assert game.get_user_chosen_card(user.id) == None
        bot1_chosen_card = game.get_user_chosen_card(bot1.id)
        assert bot1_chosen_card != None
        assert bot1_chosen_card.card_id == card2.id
        assert len(game.get_user_hand(bot1.id).cards) == 0
        assert game.get_user_hand(bot2.id).cards == [card3]

    def test_choose_cards_for_bots_errors(self):
        # Game is not STARTED
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED,
                owner_id=user.id, users=[user])
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_cards_for_bots(user.id)
            assert e.code == 400
        # Card is being placed
        game = self.create_game(status=Game.STATUS_STARTED,
                owner_id=user.id, users=[user])
        db.session.add(game)
        db.session.commit()
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_cards_for_bots(user.id)
            assert e.code == 400
        # Bots have already chosen cards
        game = self.create_game(status=Game.STATUS_STARTED,
                owner_id=user.id, users=[user])
        db.session.add(game)
        db.session.commit()
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_cards_for_bots(user.id)
            assert e.code == 400

    def test_choose_card_for_user(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card = self.create_card(1, 1)
        hand = self.create_hand(game.id, user.id, cards=[card])
        assert len(game.get_user_hand(user.id).cards) == 1
        chosen_card = game.get_user_chosen_card(user.id)
        assert chosen_card == None
        game.choose_card_for_user(user.id, card.id)
        assert len(game.get_user_hand(user.id).cards) == 0
        chosen_card = game.get_user_chosen_card(user.id)
        assert chosen_card.card_id == card.id

    def test_choose_card_for_user_errors(self):
        # Card is being placed
        user = self.create_user()
        card = self.create_card(1, 1)
        game = self.create_game(users=[user])
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_card_for_user(user.id, card.id)
            assert e.code == 400
        # User has already chosen a card
        game = self.create_game(users=[user])
        chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_card_for_user(user.id, card.id)
            assert e.code == 400
        # User tries to choose a card he doesn't own
        db.session.delete(chosen_card)
        hand = self.create_hand(game.id, user.id)
        with self.assertRaises(SixQuiPrendException) as e:
            game.choose_card_for_user(user.id, card.id)
            assert e.code == 400

    def test_choose_column_for_user(self):
        user = self.create_user()
        game = self.create_game(users=[user])
        card_one = self.create_card()
        card_two = self.create_card()
        column = self.create_column(game.id, cards=[card_two])
        user_heap = self.create_heap(game.id, user.id)
        chosen_card = self.create_chosen_card(game.id, user.id, card_one.id)
        assert column.cards == [card_two]
        assert len(user_heap.cards) == 0
        [chosen_column, new_user_heap] = game.choose_column_for_user(user.id,
                column.id)
        assert chosen_column.id == column.id
        assert chosen_column.cards == [card_one]
        assert new_user_heap.cards == [card_two]

    def test_update_status(self):
        # Users still have chosen cards to place
        user = self.create_user()
        bot = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(status=Game.STATUS_STARTED, users=[user, bot],
                owner_id=user.id)
        game.is_resolving_turn = True
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        user_hand = self.create_hand(game.id, user.id, [card])
        bot_hand = self.create_hand(game.id, bot.id)
        chosen_card = self.create_chosen_card(game.id, user.id)
        game.update_status()
        assert game.status == Game.STATUS_STARTED
        assert game.is_resolving_turn == True
        # No chosen cards, but users still have cards in hands
        db.session.delete(chosen_card)
        db.session.commit()
        game.update_status()
        assert game.status == Game.STATUS_STARTED
        assert game.is_resolving_turn == False
        # No remaining card in hands nor to place
        user_hand.cards = []
        db.session.add(user_hand)
        db.session.commit()
        game.update_status()
        assert game.status == Game.STATUS_FINISHED
        assert game.is_resolving_turn == False

if __name__ == '__main__':
    unittest.main()
