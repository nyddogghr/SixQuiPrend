from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import unittest

class TemplatesTestCase(unittest.TestCase):

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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    ################################################################################
    ## Routes
    ################################################################################

    def test_get_index(self):
        rv = self.app.get('/')
        assert rv.status_code == 200
        assert 'ng-app="SixQuiPrendApp"' in str(rv.data)

    def test_get_template(self):
        rv = self.app.get('/partial/home.html')
        assert rv.status_code == 200
        assert 'ng-controller="HomeController"' in str(rv.data)

if __name__ == '__main__':
    unittest.main()
