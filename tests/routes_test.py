from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models import *
from sixquiprend.routes import *
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class RoutesTestCase(unittest.TestCase):

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

    def login_admin(self):
        rv = self.app.post('/login', data=json.dumps(dict(
            username=self.ADMIN_USERNAME,
            password=self.ADMIN_PASSWORD,
        )), content_type='application/json')
        assert rv.status_code == 201

    def logout(self):
        rv = self.app.post('/logout', content_type='application/json')
        assert rv.status_code == 201

    def get_current_user(self):
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        result = json.loads(rv.data)
        if result['status'] == True:
            return User.query.get(result['user']['id'])

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
        card = Card(number, cow_value)
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

class IndexTestCase(RoutesTestCase):

    def test_get_index(self):
        rv = self.app.get('/')
        assert rv.status_code == 200
        assert 'ng-app="SixQuiPrendApp"' in str(rv.data)

class LoginLogoutTestCase(RoutesTestCase):

    def test_login_logout(self):
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        assert json.loads(rv.data) == {'status':False}

        self.login()
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        response = json.loads(rv.data)
        assert response['status'] == True
        assert response['user']['username'] == self.USERNAME

        self.logout()
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        assert json.loads(rv.data) == {'status':False}

    def test_login_errors(self):
        # Bot login
        bot_username = 'bot'
        bot_password = 'bot'
        bot = User(username=bot_username,
                password=bcrypt.hash(bot_password),
                active=True, urole=User.BOT_ROLE)
        db.session.add(bot)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=bot_username,
            password=bot_password,
        )), content_type='application/json')
        assert rv.status_code == 401
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        assert json.loads(rv.data) == {'status':False}

        # User not present
        rv = self.app.post('/login', data=json.dumps(dict(
            username='nope',
            password='nope',
        )), content_type='application/json')
        assert rv.status_code == 404

        # User inactive
        user = self.create_user(False)
        rv = self.app.post('/login', data=json.dumps(dict(
            username=user.username,
            password='Password',
        )), content_type='application/json')
        assert rv.status_code == 403

        # Bad password
        user = self.create_user()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=user.username,
            password='nope'
        )), content_type='application/json')
        assert rv.status_code == 400

class UsersTestCase(RoutesTestCase):

    def test_register(self):
        username = 'toto'
        password = 'toto'
        rv = self.app.post('/users/register', data=json.dumps(dict(
            username=username,
            password=password,
        )), content_type='application/json')
        assert rv.status_code == 201
        new_user = User.query.filter(username == username,
                password == password).first()
        assert new_user != None

    def test_register_errors(self):
        # User already present
        username = User.query.first().username
        password = 'Password'
        rv = self.app.post('/users/register', data=json.dumps(dict(
            username=username,
            password=password,
        )), content_type='application/json')
        assert rv.status_code == 400

        # Registering deactivated
        allow_register_users = app.config['ALLOW_REGISTER_USERS']
        app.config['ALLOW_REGISTER_USERS'] = False
        username = User.query.first().username
        password = 'Password'
        rv = self.app.post('/users/register', data=json.dumps(dict(
            username=username,
            password=password,
        )), content_type='application/json')
        assert rv.status_code == 403
        app.config['ALLOW_REGISTER_USERS'] = allow_register_users

    def test_get_users(self):
        user = self.create_user()
        self.login()
        rv = self.app.get('/users')
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 3
        assert users[-1]['username'] == user.username

        # Test limit and offset
        rv = self.app.get('/users', query_string=dict(limit=1))
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 1
        assert users[-1]['username'] != user.username
        rv = self.app.get('/users', query_string=dict(limit=1, offset=2))
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 1
        assert users[-1]['username'] == user.username

    def test_activate_users(self):
        user = self.create_user(False)
        self.login_admin()
        db.session.refresh(user)
        assert user.active == False
        rv = self.app.put('/users/'+str(user.id)+'/activate')
        assert rv.status_code == 200
        db.session.refresh(user)
        assert user.active == True

    def test_activate_users_errors(self):
        # Current user not admin
        user = self.create_user(False)
        self.login()
        rv = self.app.put('/users/'+str(user.id)+'/activate')
        assert rv.status_code == 401

        # User not found
        self.login_admin()
        rv = self.app.put('/users/0/activate')
        assert rv.status_code == 404

    def test_deactivate_users(self):
        user = self.create_user()
        self.login_admin()
        db.session.refresh(user)
        assert user.active == True
        rv = self.app.put('/users/'+str(user.id)+'/deactivate')
        assert rv.status_code == 200
        db.session.refresh(user)
        assert user.active == False

    def test_deactivate_users_errors(self):
        # Current user not admin
        user = self.create_user()
        self.login()
        rv = self.app.put('/users/'+str(user.id)+'/deactivate')
        assert rv.status_code == 401

        # User not found
        self.login_admin()
        rv = self.app.put('/users/0/deactivate')
        assert rv.status_code == 404

    def test_delete_users(self):
        user = self.create_user()
        self.login_admin()
        db.session.refresh(user)
        assert User.query.get(user.id) != None
        rv = self.app.delete('/users/'+str(user.id))
        assert rv.status_code == 200
        assert User.query.get(user.id) == None

    def test_delete_users_errors(self):
        # Current user not admin
        user = self.create_user()
        self.login()
        rv = self.app.delete('/users/'+str(user.id))
        assert rv.status_code == 401

        # User not found
        self.login_admin()
        rv = self.app.delete('/users/0')
        assert rv.status_code == 404

class GamesTestCase(RoutesTestCase):

    def test_get_games(self):
        game1 = self.create_game()
        game2 = self.create_game()
        rv = self.app.get('/games')
        assert rv.status_code == 200
        games =  json.loads(rv.data)['games']
        assert len(games) == 2
        assert games[0]['id'] == game1.id
        assert games[1]['id'] == game2.id

        # Test limit and offset
        rv = self.app.get('/games', query_string=dict(limit=1))
        assert rv.status_code == 200
        games =  json.loads(rv.data)['games']
        assert len(games) == 1
        assert games[0]['id'] == game1.id
        rv = self.app.get('/games', query_string=dict(limit=1, offset=1))
        assert rv.status_code == 200
        games =  json.loads(rv.data)['games']
        assert len(games) == 1
        assert games[0]['id'] == game2.id

    def test_get_game(self):
        game = self.create_game()
        self.login()
        rv = self.app.get('/games/'+str(game.id))
        assert rv.status_code == 200
        game_response = json.loads(rv.data)['game']
        assert game_response['id'] == game.id

    def test_get_game_errors(self):
        # Game not found
        self.login()
        rv = self.app.get('/games/0')
        assert rv.status_code == 404

    def test_create_game(self):
        self.login()
        rv = self.app.post('/games', content_type='application/json')
        assert rv.status_code == 201
        game = json.loads(rv.data)['game']
        assert game['status'] == Game.STATUS_CREATED
        assert game['users'][0]['username'] == self.USERNAME

    def test_delete_game(self):
        game = self.create_game()
        self.login_admin()
        rv = self.app.delete('/games/'+str(game.id))
        assert rv.status_code == 204
        game_db = Game.query.get(game.id)
        assert game_db == None

    def test_delete_game_errors(self):
        # User not admin
        game = self.create_game()
        self.login()
        rv = self.app.delete('/games/'+str(game.id))
        assert rv.status_code == 401

        # Game not found
        self.login_admin()
        rv = self.app.delete('/games/0')
        assert rv.status_code == 404

class GamesActionsTestCase(RoutesTestCase):

    def test_game_enter(self):
        game = self.create_game()
        self.login()
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 201
        game_result = json.loads(rv.data)['game']
        assert len(game_result['users']) == 1
        assert game_result['users'][0]['id'] == self.get_current_user().id

    def test_game_enter_errors(self):
        # Game not found
        self.login()
        rv = self.app.post('/games/0/enter')
        assert rv.status_code == 404

        # Game not CREATED
        game = self.create_game(Game.STATUS_STARTED)
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 400

        # User already in
        game = self.create_game()
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 201
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 400

        # Game complete
        max_player_number = app.config['MAX_PLAYER_NUMBER']
        app.config['MAX_PLAYER_NUMBER'] = 1
        game = self.create_game()
        user = self.create_user()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 400
        app.config['MAX_PLAYER_NUMBER'] = 1

    def test_game_get_bots(self):
        bot1 = self.create_user(urole=User.BOT_ROLE)
        bot2 = self.create_user(urole=User.BOT_ROLE)
        game = self.create_game()
        game.users.append(bot1)
        game.owner_id = bot1.id
        db.session.add(game)
        db.session.commit()
        self.login()
        rv = self.app.get('/games/'+str(game.id)+'/users/bots')
        assert rv.status_code == 200
        bots = json.loads(rv.data)['available_bots']
        assert len(bots) == 1
        assert bots[0]['id'] == bot2.id

    def test_game_get_bots_errors(self):
        self.login()
        rv = self.app.get('/games/0/users/bots')
        assert rv.status_code == 404

    def test_game_add_bot(self):
        self.login()
        bot1 = self.create_user(urole=User.BOT_ROLE)
        bot2 = self.create_user(urole=User.BOT_ROLE)
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        game.users.append(bot1)
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot2.id)+'/add')
        assert rv.status_code == 201
        game_result = json.loads(rv.data)['game']
        assert len(game_result['users']) == 3

    def test_game_add_bot_errors(self):
        # Game not found
        self.login()
        bot = self.create_user(urole=User.BOT_ROLE)
        rv = self.app.post('/games/0/users/'+str(bot.id)+'/add')
        assert rv.status_code == 404

        # User not game owner
        game = self.create_game()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot.id)+'/add')
        assert rv.status_code == 403

        # Game not CREATED
        game = self.create_game(Game.STATUS_STARTED)
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot.id)+'/add')
        assert rv.status_code == 400

        # Bot already present
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        game.users.append(bot)
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot.id)+'/add')
        assert rv.status_code == 400

        # Game complete
        max_player_number = app.config['MAX_PLAYER_NUMBER']
        app.config['MAX_PLAYER_NUMBER'] = 1
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot.id)+'/add')
        assert rv.status_code == 400
        app.config['MAX_PLAYER_NUMBER'] = max_player_number

        # Bot not found
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/0/add')
        assert rv.status_code == 404

        # Bot added not really a bot
        fake_bot = self.create_user()
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(fake_bot.id)+'/add')
        assert rv.status_code == 400

    def test_game_leave(self):
        # User is game owner
        self.login()
        game = self.create_game()
        user = self.create_user()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.users.append(user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.put('/games/'+str(game.id)+'/leave')
        assert rv.status_code == 200
        game_result = json.loads(rv.data)['game']
        assert game_result['owner_id'] == user.id

        # User is not game owner
        game.users.append(current_user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.put('/games/'+str(game.id)+'/leave')
        assert rv.status_code == 200
        game_result = json.loads(rv.data)['game']
        assert game_result['owner_id'] == user.id

    def test_game_leave_errors(self):
        # Game not found
        self.login()
        rv = self.app.put('/games/0/leave')
        assert rv.status_code == 404

        # User not in game
        game = self.create_game()
        rv = self.app.put('/games/'+str(game.id)+'/leave')
        assert rv.status_code == 400

        # User only non-bot player
        current_user = self.get_current_user()
        bot = self.create_user(urole=User.BOT_ROLE)
        game.users.append(current_user)
        game.users.append(bot)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.put('/games/'+str(game.id)+'/leave')
        assert rv.status_code == 400

    def test_game_start(self):
        self.login()
        game = self.create_game(status=Game.STATUS_CREATED)
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        user = self.create_user()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        add_cards()
        rv = self.app.put('/games/'+str(game.id)+'/start')
        assert rv.status_code == 200
        game_result = json.loads(rv.data)['game']
        assert game_result['status'] == Game.STATUS_STARTED

    def test_game_start_errors(self):
        # Game not found
        self.login()
        rv = self.app.put('/games/0/start')
        assert rv.status_code == 404

        # User not game owner
        game = self.create_game(status=Game.STATUS_CREATED)
        user1 = self.create_user()
        user2 = self.create_user()
        game.users.append(user1)
        game.users.append(user2)
        db.session.add(game)
        db.session.commit()
        rv = self.app.put('/games/'+str(game.id)+'/start')
        assert rv.status_code == 403

        # Not enough users
        game = self.create_game(status=Game.STATUS_CREATED)
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        rv = self.app.put('/games/'+str(game.id)+'/start')
        assert rv.status_code == 400

        # Game not CREATED
        game = self.create_game(status=Game.STATUS_STARTED)
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        rv = self.app.put('/games/'+str(game.id)+'/start')
        assert rv.status_code == 400

class GamesTurnsTestCase(RoutesTestCase):

    def test_get_columns(self):
        self.login()
        game = self.create_game(status=Game.STATUS_STARTED)
        card = self.create_card()
        column = self.create_column(game_id=game.id, cards=[card])
        rv = self.app.get('/games/'+str(game.id)+'/columns')
        assert rv.status_code == 200
        response_columns = json.loads(rv.data)['columns']
        assert len(response_columns) == 1
        assert len(response_columns[0]['cards']) == 1
        assert response_columns[0]['cards'][0] == card.serialize()

    def test_get_columns_errors(self):
        # Game not found
        self.login()
        rv = self.app.get('/games/0/columns')
        assert rv.status_code == 404

        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        rv = self.app.get('/games/'+str(game.id)+'/columns')
        assert rv.status_code == 400

    def test_get_users(self):
        self.login()
        game = self.create_game()
        user = self.create_user()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/users')
        assert rv.status_code == 200
        response_users = json.loads(rv.data)['users']
        assert len(response_users) == 1
        assert response_users[0]['id'] == user.id

    def test_get_users_errors(self):
        # Game not found
        self.login()
        rv = self.app.get('/games/0/users')
        assert rv.status_code == 404

    def test_get_user_status(self):
        self.login()
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/status')
        assert rv.status_code == 200
        response_status = json.loads(rv.data)['user']
        assert response_status['id'] == user.id
        assert response_status['has_chosen_card'] == False
        assert response_status['needs_to_choose_column'] == False

        self.create_chosen_card(game.id, user.id)
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/status')
        assert rv.status_code == 200
        response_status = json.loads(rv.data)['user']
        assert response_status['has_chosen_card'] == True

    def test_get_user_status_errors(self):
        # Game not found
        self.login()
        user = self.create_user()
        rv = self.app.get('/games/0/users/'+str(user.id)+'/status')
        assert rv.status_code == 404

        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/status')
        assert rv.status_code == 400

        # User not in game
        game = self.create_game(status=Game.STATUS_STARTED)
        rv = self.app.get('/games/'+str(game.id)+'/users/0/status')
        assert rv.status_code == 404

    def test_get_user_heap(self):
        self.login()
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        heap = self.create_heap(game.id, user.id, [card])
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/heap')
        assert rv.status_code == 200
        response_heap = json.loads(rv.data)['heap']
        assert len(response_heap['cards']) == 1
        assert response_heap['cards'][0]['id'] == card.id

    def test_get_user_heap_errors(self):
        # Game not found
        self.login()
        user = self.create_user()
        rv = self.app.get('/games/0/users/'+str(user.id)+'/heap')
        assert rv.status_code == 404

        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/heap')
        assert rv.status_code == 400

        # User not in game
        game = self.create_game(status=Game.STATUS_STARTED)
        rv = self.app.get('/games/'+str(game.id)+'/users/'+str(user.id)+'/heap')
        assert rv.status_code == 404

    def test_get_current_user_hand(self):
        self.login()
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        card = self.create_card()
        hand = self.create_hand(game.id, user.id, [card])
        rv = self.app.get('/games/'+str(game.id)+'/users/current/hand')
        assert rv.status_code == 200
        response_hand = json.loads(rv.data)['hand']
        assert len(response_hand['cards']) == 1
        assert response_hand['cards'][0]['id'] == card.id

    def test_get_current_user_hand_errors(self):
        # Game not found
        self.login()
        rv = self.app.get('/games/0/users/current/hand')
        assert rv.status_code == 404

        # Game not started
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_CREATED)
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/users/current/hand')
        assert rv.status_code == 400

        # User not in game
        game = self.create_game(status=Game.STATUS_STARTED)
        rv = self.app.get('/games/'+str(game.id)+'/users/current/hand')
        assert rv.status_code == 404

    def test_choose_card(self):
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
        assert response_chosen_card['card_id'] == card.id

    def test_choose_card_errors(self):
        # Game not found
        self.login()
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        card = self.create_card()
        rv = self.app.post('/games/0/card/'+str(card.id))
        assert rv.status_code == 404

        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        game.users.append(user)
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 400

        # User not in game
        game = self.create_game(status=Game.STATUS_STARTED)
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 400

        # Card already chosen
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 400

        # Card not owned
        db.session.delete(chosen_card)
        hand = self.create_hand(game_id=game.id, user_id=user.id)
        rv = self.app.post('/games/'+str(game.id)+'/card/'+str(card.id))
        assert rv.status_code == 400

    def test_get_chosen_cards(self):
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
        user_chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        user2_chosen_card = self.create_chosen_card(game.id, user2.id, card2.id)
        rv = self.app.get('/games/'+str(game.id)+'/chosen_cards')
        assert rv.status_code == 200
        response_chosen_cards = sorted(json.loads(rv.data)['chosen_cards'],
                key=lambda chosen_card: chosen_card['user_id'])
        assert len(response_chosen_cards) == 2
        for response_chosen_card in response_chosen_cards:
            assert response_chosen_card['game_id'] == game.id
        assert response_chosen_cards[0]['user_id'] == user.id
        assert response_chosen_cards[0]['card_id'] == card.id
        assert response_chosen_cards[1]['user_id'] == user2.id
        assert response_chosen_cards[1]['card_id'] == card2.id

    def test_get_chosen_cards_errors(self):
        # Game not found
        self.login()
        rv = self.app.get('/games/0/chosen_cards')
        assert rv.status_code == 404

        # Game not started
        self.login()
        game = self.create_game(status=Game.STATUS_CREATED)
        rv = self.app.get('/games/'+str(game.id)+'/chosen_cards')
        assert rv.status_code == 400

        # Some users have not chosen a card yet
        self.login()
        user = self.get_current_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.get('/games/'+str(game.id)+'/chosen_cards')
        assert rv.status_code == 400

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

    def test_resolve_turn_errors(self):
        # Game not found
        self.login()
        rv = self.app.post('/games/0/turns/resolve')
        assert rv.status_code == 404

        # Game not started
        game = self.create_game(status=Game.STATUS_CREATED)
        rv = self.app.post('/games/'+str(game.id)+'/turns/resolve')
        assert rv.status_code == 400

        # User not game owner
        game = self.create_game(status=Game.STATUS_STARTED)
        user = self.get_current_user()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/turns/resolve')
        assert rv.status_code == 403

        # No card to place
        user2 = self.create_user()
        game = self.create_game(status=Game.STATUS_STARTED)
        game.users.append(user)
        game.users.append(user2)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/turns/resolve')
        assert rv.status_code == 400

        # User must choose a column
        card = self.create_card(1, 1)
        card2 = self.create_card(2, 2)
        card3 = self.create_card(3, 3)
        user_chosen_card = self.create_chosen_card(game.id, user.id, card.id)
        user2_chosen_card = self.create_chosen_card(game.id, user2.id, card2.id)
        column = self.create_column(game.id, [card3])
        rv = self.app.post('/games/'+str(game.id)+'/turns/resolve')
        assert rv.status_code == 422
        assert json.loads(rv.data)['user_id'] == user.id

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

    def test_choose_column_for_card_errors(self):
        # Game not found
        self.login()
        game = self.create_game(status=Game.STATUS_CREATED)
        column = self.create_column(game.id)
        rv = self.app.post('/games/0/columns/'+str(column.id)+'/choose')
        assert rv.status_code == 404

        # Game not started
        rv = self.app.post('/games/'+str(game.id)+'/columns/'+str(column.id)+'/choose')
        assert rv.status_code == 400

        # User not in game
        game = self.create_game(status=Game.STATUS_STARTED)
        column = self.create_column(game.id)
        rv = self.app.post('/games/'+str(game.id)+'/columns/'+str(column.id)+'/choose')
        assert rv.status_code == 400

        # Column not found
        user = self.get_current_user()
        game.users.append(user)
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/columns/0/choose')
        assert rv.status_code == 404

        # No card to place
        rv = self.app.post('/games/'+str(game.id)+'/columns/'+str(column.id)+'/choose')
        assert rv.status_code == 400

if __name__ == '__main__':
    unittest.main()
