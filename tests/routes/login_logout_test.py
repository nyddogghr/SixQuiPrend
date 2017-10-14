from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class LoginLogoutTestCase(unittest.TestCase):

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

    def logout(self):
        rv = self.app.post('/logout', content_type='application/json')
        assert rv.status_code == 201

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

    def test_login_errors_bot_login(self):
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

    def test_login_errors_user_not_present(self):
        rv = self.app.post('/login', data=json.dumps(dict(
            username='nope',
            password='nope',
        )), content_type='application/json')
        assert rv.status_code == 404

    def test_login_errors_user_inactive(self):
        user = self.create_user(False)
        rv = self.app.post('/login', data=json.dumps(dict(
            username=user.username,
            password='Password',
        )), content_type='application/json')
        assert rv.status_code == 403

    def test_login_errors_bad_password(self):
        user = self.create_user()
        rv = self.app.post('/login', data=json.dumps(dict(
            username=user.username,
            password='nope'
        )), content_type='application/json')
        assert rv.status_code == 400

if __name__ == '__main__':
    unittest.main()
