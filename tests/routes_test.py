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
        if not User.query.filter(User.username == self.USERNAME).first():
            user = User(username=self.USERNAME,
                    password=bcrypt.hash(self.PASSWORD),
                    active=True)
            db.session.add(user)
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

    def logout(self):
        rv = self.app.post('/logout', content_type='application/json')
        assert rv.status_code == 201

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
        username = 'toto'
        password = 'toto'
        user = User(username=username,
                password=bcrypt.hash(password),
                active=False)
        db.session.add(user)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=username,
            password=password,
        )), content_type='application/json')
        assert rv.status_code == 403

        # Bad password
        user.active = True
        db.session.add(user)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=username,
            password=password + 'nope',
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
        assert new_user.active == True

    def test_register_errors(self):
        # User already present
        user = User.query.first()
        username = user.username
        password = 'toto'
        rv = self.app.post('/users/register', data=json.dumps(dict(
            username=username,
            password=password,
        )), content_type='application/json')
        assert rv.status_code == 400

    def test_get_users(self):
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password))
        db.session.add(user2)
        db.session.commit()
        self.login()
        rv = self.app.get('/users')
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 2
        assert users[-1]['username'] == username

        # limit and offset
        rv = self.app.get('/users', query_string=dict(limit=1))
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 1
        assert users[-1]['username'] != username
        rv = self.app.get('/users', query_string=dict(limit=1, offset=1))
        assert rv.status_code == 200
        users = json.loads(rv.data)['users']
        assert len(users) == 1
        assert users[-1]['username'] == username

    def test_activate_users(self):
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password),
                active=False)
        db.session.add(user2)
        db.session.commit()
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        db.session.refresh(user2)
        assert user2.active == False
        rv = self.app.put('/users/'+str(user2.id)+'/activate')
        assert rv.status_code == 200
        db.session.refresh(user2)
        assert user2.active == True

    def test_activate_users_errors(self):
        # Current user not admin
        self.login()
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password),
                active=False)
        db.session.add(user2)
        db.session.commit()
        rv = self.app.put('/users/'+str(user2.id)+'/activate')
        assert rv.status_code == 401
        # User not found
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        rv = self.app.put('/users/0/activate')
        assert rv.status_code == 404

    def test_deactivate_users(self):
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password))
        db.session.add(user2)
        db.session.commit()
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        db.session.refresh(user2)
        assert user2.active == True
        rv = self.app.put('/users/'+str(user2.id)+'/deactivate')
        assert rv.status_code == 200
        db.session.refresh(user2)
        assert user2.active == False

    def test_deactivate_users_errors(self):
        # Current user not admin
        self.login()
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password))
        db.session.add(user2)
        db.session.commit()
        rv = self.app.put('/users/'+str(user2.id)+'/deactivate')
        assert rv.status_code == 401
        # User not found
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        rv = self.app.put('/users/0/deactivate')
        assert rv.status_code == 404

    def test_delete_users(self):
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password))
        db.session.add(user2)
        db.session.commit()
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        db.session.refresh(user2)
        assert User.query.get(user2.id) != None
        rv = self.app.delete('/users/'+str(user2.id))
        assert rv.status_code == 200
        assert User.query.get(user2.id) == None

    def test_delete_users_errors(self):
        # Current user not admin
        self.login()
        username = 'toto'
        password = 'toto'
        user2 = User(username=username,
                password = bcrypt.hash(password))
        db.session.add(user2)
        db.session.commit()
        rv = self.app.delete('/users/'+str(user2.id))
        assert rv.status_code == 401
        # User not found
        admin_username = 'admin'
        admin_password = 'admin'
        admin = User(username=admin_username,
                password = bcrypt.hash(admin_password),
                urole=User.ADMIN_ROLE)
        db.session.add(admin)
        db.session.commit()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=admin_username,
            password=admin_password
        )), content_type='application/json')
        assert rv.status_code == 201
        rv = self.app.delete('/users/0')
        assert rv.status_code == 404

class GameTestCase(RoutesTestCase):

    def test_get_games(self):
        rv = self.app.get('/games')
        assert rv.status_code == 200
        assert json.loads(rv.data) == {'games':[]}

    def test_create_game(self):
        rv = self.app.get('/games')
        assert json.loads(rv.data) == {'games':[]}
        assert rv.status_code == 200
        rv = self.app.post('/games', content_type='application/json')
        assert rv.status_code == 401

        self.login()
        rv = self.app.post('/games', content_type='application/json')
        assert rv.status_code == 201
        game = json.loads(rv.data)['game']
        assert game['status'] == Game.STATUS_CREATED
        assert game['users'][0]['username'] == self.USERNAME

if __name__ == '__main__':
    unittest.main()
