from flask import request, session, \
     render_template, jsonify
from sixquiprend.sixquiprend import app
from flask_login import login_required, current_user, \
     login_user, logout_user
from sixquiprend.models import *
from functools import wraps

def admin_required(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if not current_user.is_admin():
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return func_wrapper

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter(User.username == request.json['username']).first()
    if user:
        if not user.is_active:
            return jsonify(logged_in=False, error='User is inactive'), 400
        if user.verify_password(request.json['password']):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return jsonify(logged_in=True)
        else:
            return jsonify(logged_in=False, error='Password is invalid'), 400
    else:
        return jsonify(logged_in=False, error='User doesn\'t exist'), 404

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return jsonify(logged_out=False)

@app.route('/register', methods=['POST'])
def register():
    user = User.query.filter(User.username == request.json['username']).first()
    if not user:
        user = User(username=request.json['username'],
                password=bcrypt.encrypt(request.json['password']))
        db.session.add(user)
        db.session.commit()
        return jsonify(registered=True)
    else:
        return jsonify(registered=False, error='User already exists'), 400

@app.route('/users/<int:user_id>/activate', methods=['PUT'])
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.active = True
        db.session.add(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(status=False, error='User doesn\'t exist'), 404

@app.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@login_required
@admin_required
def deactivate_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.active = False
        db.session.add(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(status=False, error='User doesn\'t exist'), 404

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(status=False, error='User doesn\'t exist'), 404

@app.route('/users/current')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify(id=current_user.id, username=current_user.username, is_logged_in=True)
    else:
        return jsonify(is_logged_in=False)

@app.route('/games')
def get_games():
    games = Game.query.all()
    return jsonify(games=games)

@app.route('/games/<int:game_id>')
def get_game(game_id):
    game = Game.query.get(game_id)
    return jsonify(game=game)

@app.route('/games', methods=['POST'])
@login_required
def create_game():
    game = Game()
    game.users.append(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/enter', methods=['POST'])
@login_required
def enter_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.CREATED:
        return jsonify(error='Cannot enter already started game'), 400
    game.users.append(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/leave', methods=['POST'])
@login_required
def leave_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if current_user not in game.users:
        return jsonify(error='Not in game'), 400
    game.users.remove(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/start', methods=['PUT'])
@login_required
def start_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if not game.status != Game.CREATED:
        return jsonify(error='Cannot start an already started game'), 400
    if game.users.length < 2:
        return jsonify(error='Cannot start game with less than 2 players'), 400
    game.status = Game.STARTED
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game)

@app.route('/games/<int:game_id>/columns')
@login_required
def get_game_columns(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    columns = Column.query.filter(game_id=game_id).all()
    return jsonify(columns=columns)

@app.route('/games/<int:game_id>/users')
@login_required
def get_game_users(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    return jsonify(users=users)

@app.route('/games/<int:game_id>/users/<int:user_id>/status')
@login_required
def get_user_game_status(game_id, user_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    user = game.users.query.get(id=user_id)
    if not user:
        return jsonify(error='No user found'), 404
    response = user.serialize()
    response['chosen_card'] = ChosenCard.query.filter(
            user_id=user_id,
            game_id=game_id).count()
    return jsonify(user=response)

@app.route('/games/<int:game_id>/users/<int:user_id>/heaps')
@login_required
def get_user_game_heaps(game_id, user_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    user = game.users.query.get(id=user_id)
    if not user:
        return jsonify(error='No user found'), 404
    heaps = Heap.query.filter(game_id=game_id, user_id=user_id).all()
    return jsonify(heaps=heaps)

@app.route('/games/<int:game_id>/users/<int:user_id>/hand')
@login_required
def get_user_game_hand(game_id, user_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    user = game.users.query.get(id=user_id)
    if not user:
        return jsonify(error='No user found'), 404
    hand = Hand.query.filter(game_id=game_id, user_id=user_id).first()
    return jsonify(hand=hand)

@app.route('/games/<int:game_id>/card/<int:card_id>', methods=['POST'])
@login_required
def choose_card_for_game(game_id, card_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    user = game.users.query.get(id=user_id)
    if not user:
        return jsonify(error='No user found'), 404
    if ChosenCard.query.filter(game_id=game_id,
            user_id=current_user.id).count() > 0:
        return jsonify(error='Card already chosen'), 400
    chosen_card = ChosenCard(game_id=game_id, user_id=current_user.id,
            card_id=card_id)
    db.session.add(chosen_card)
    db.session.commit()
    return jsonify(chosen_card=chosen_card), 201
