from flask import Flask
from passlib.hash import bcrypt
from sixquiprend.config import *
from sixquiprend.models import *
from sixquiprend.routes import *
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
        rv = self.app.get('/games/'+str(game.id))
        assert rv.status_code == 200
        game_response = json.loads(rv.data)['game']
        assert game_response['id'] == game.id

    def test_get_game_errors_game_not_found(self):
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

    def test_delete_game_errors_not_admin(self):
        game = self.create_game()
        self.login()
        rv = self.app.delete('/games/'+str(game.id))
        assert rv.status_code == 401

    def test_delete_game_errors_game_not_found(self):
        self.login_admin()
        rv = self.app.delete('/games/0')
        assert rv.status_code == 404

if __name__ == '__main__':
    unittest.main()
