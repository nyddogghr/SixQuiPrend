from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models.game import Game
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class GamesTestCase(unittest.TestCase):

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
                urole=User.ROLE_ADMIN)
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

    def get_current_user(self):
        rv = self.app.get('/users/current')
        assert rv.status_code == 200
        result = json.loads(rv.data)
        if result['user'] != {}:
            return User.find(result['user']['id'])

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

    def create_game(self, status=Game.STATUS_CREATED, users=[], owner_id=None):
        game = Game(status=status)
        for user in users:
            game.users.append(user)
        game.owner_id = owner_id
        db.session.add(game)
        db.session.commit()
        return game

    ################################################################################
    ## Routes
    ################################################################################

    def test_get_games(self):
        game1 = self.create_game()
        game2 = self.create_game()
        rv = self.app.get('/games')
        assert rv.status_code == 200
        games = json.loads(rv.data)['games']
        assert len(games) == 2
        assert games[0]['id'] == game1.id
        assert games[1]['id'] == game2.id

        # Test limit and offset
        rv = self.app.get('/games', query_string=dict(limit=1))
        assert rv.status_code == 200
        games = json.loads(rv.data)['games']
        assert len(games) == 1
        assert games[0]['id'] == game1.id
        rv = self.app.get('/games', query_string=dict(limit=1, offset=1))
        assert rv.status_code == 200
        games = json.loads(rv.data)['games']
        assert len(games) == 1
        assert games[0]['id'] == game2.id

    def test_count_games(self):
        game1 = self.create_game()
        game2 = self.create_game()
        rv = self.app.get('/games/count')
        assert rv.status_code == 200
        count = json.loads(rv.data)['count']
        assert count == 2

    def test_get_game(self):
        game = self.create_game()
        self.login()
        rv = self.app.get('/games/' + str(game.id))
        assert rv.status_code == 200
        game_response = json.loads(rv.data)['game']
        assert game_response['id'] == game.id

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

    def test_enter_game(self):
        self.login()
        game = self.create_game(status=Game.STATUS_CREATED)
        rv = self.app.post('/games/' + str(game.id) + '/enter', content_type='application/json')
        assert rv.status_code == 201
        game = json.loads(rv.data)['game']
        assert game['status'] == Game.STATUS_CREATED
        assert game['users'][0]['username'] == self.USERNAME

    def test_get_available_bots_for_game(self):
        self.login()
        bot = self.create_user(urole=User.ROLE_BOT)
        game = self.create_game(status=Game.STATUS_CREATED,
                owner_id=self.get_current_user().id)
        rv = self.app.get('/games/' + str(game.id) + '/users/bots')
        assert rv.status_code == 200
        available_bots = json.loads(rv.data)['available_bots']
        assert available_bots == [bot.serialize()]

    def test_add_bot_to_game(self):
        self.login()
        game = self.create_game(status=Game.STATUS_CREATED,
                owner_id=self.get_current_user().id)
        bot = self.create_user(urole=User.ROLE_BOT)
        rv = self.app.post('/games/' + str(game.id) + '/users/' + str(bot.id) +
                '/add')
        assert rv.status_code == 201
        game = json.loads(rv.data)['game']
        assert game['users'] == [bot.serialize()]

    def test_leave_game(self):
        self.login()
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED,
                users=[self.get_current_user(), user],
                owner_id=self.get_current_user().id)
        rv = self.app.put('/games/' + str(game.id) + '/leave')
        assert rv.status_code == 200
        game = json.loads(rv.data)['game']
        assert game['users'] == [user.serialize()]

    def test_start_game(self):
        add_cards()
        self.login()
        user = self.create_user()
        game = self.create_game(status=Game.STATUS_CREATED,
                users=[self.get_current_user(), user],
                owner_id=self.get_current_user().id)
        rv = self.app.put('/games/' + str(game.id) + '/start')
        assert rv.status_code == 200
        game = json.loads(rv.data)['game']
        assert game['status'] == Game.STATUS_STARTED

if __name__ == '__main__':
    unittest.main()
