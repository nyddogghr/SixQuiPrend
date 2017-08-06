from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models import *
from sixquiprend.routes import *
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class SixquiprendTestCase(unittest.TestCase):

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
        with app.app_context():
            db.create_all()
            if not User.query.filter(User.username == 'User').first():
                user = User(username=self.USERNAME,
                        password=bcrypt.hash(self.PASSWORD),
                        active=True)
                db.session.add(user)
                db.session.commit()

    def tearDown(self):
        self.app = app.test_client()
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with app.app_context():
            self.app.post('/login', data=json.dumps(dict(
                username=self.USERNAME,
                password=self.PASSWORD,
            )), content_type='application/json')

    def logout(self):
        with app.app_context():
            self.app.post('/logout', content_type='application/json')

    def test_get_games(self):
        rv = self.app.get('/games')
        assert rv.status_code == 200
        assert json.loads(rv.data) == {'games':[]}

    def test_create_game(self):
        rv = self.app.get('/games')
        assert json.loads(rv.data) == {'games':[]}
        rv = self.app.post('/games')
        assert rv.status_code == 401

        self.login()
        rv = self.app.post('/games', content_type='application/json')
        assert rv.status_code == 201
        game = json.loads(rv.data)['game']
        assert game['status'] == Game.GAME_STATUS_CREATED
        assert len(game['users'])== 1

if __name__ == '__main__':
    unittest.main()
