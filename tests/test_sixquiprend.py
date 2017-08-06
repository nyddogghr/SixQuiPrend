from sixquiprend.sixquiprend import app, db
from passlib.hash import bcrypt
from flask import Flask
import unittest
from sixquiprend.config import *
from sixquiprend.utils import *
from sixquiprend.models import *
from sixquiprend.routes import *
import json

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
                        password=bcrypt.encrypt(self.PASSWORD),
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
            self.app.post('/login', data=dict(
                username=self.USERNAME,
                password=self.PASSWORD,
            ), follow_redirects=True)

    def logout(self):
        with app.app_context():
            self.app.get('/logout', follow_redirects=True)

    def test_get_games(self):
        rv = self.app.get('/games')
        assert json.loads(rv.data) == {'games':[]}

if __name__ == '__main__':
    unittest.main()
