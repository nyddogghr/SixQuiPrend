from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models.card import Card
from sixquiprend.sixquiprend import app, db
from sixquiprend.utils import *
import json
import random
import unittest

class CardTestCase(unittest.TestCase):

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
        card = self.create_card(1, 1)
        assert Card.find(card.id) == card

    def test_find_errors(self):
        with self.assertRaises(SixQuiPrendException) as e:
            Card.find(-1)
            assert e.code == 404

if __name__ == '__main__':
    unittest.main()
