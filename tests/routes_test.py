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

    def tes_get_game_errors(self):
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
        app.config['MAX_PLAYER_NUMBER'] = 1
        game = self.create_game()
        user = self.create_user()
        game.users.append(user)
        game.owner_id = user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/enter')
        assert rv.status_code == 400

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
        app.config['MAX_PLAYER_NUMBER'] = 1
        game = self.create_game()
        current_user = self.get_current_user()
        game.users.append(current_user)
        game.owner_id = current_user.id
        db.session.add(game)
        db.session.commit()
        rv = self.app.post('/games/'+str(game.id)+'/users/'+str(bot.id)+'/add')
        assert rv.status_code == 400

        # Bot not found
        app.config['MAX_PLAYER_NUMBER'] = 5
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

if __name__ == '__main__':
    unittest.main()
