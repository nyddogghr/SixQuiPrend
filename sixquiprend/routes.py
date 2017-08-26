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
        if not current_user.get_urole() >= User.USER_ADMIN_ROLE:
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return func_wrapper

def bot_forbidden(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if not current_user.get_urole() > User.USER_BOT_ROLE:
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return func_wrapper

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user = User.query \
            .filter(User.username == request.get_json()['username']).first()
    if user:
        if not user.is_active:
            return jsonify(logged_in=False, error='User is inactive'), 400
        if user.verify_password(request.get_json()['password']):
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
    user = User.query \
            .filter(User.username == request.get_json()['username']).first()
    if not user:
        user = User(username=request.get_json()['username'],
                password=bcrypt.hash(request.get_json()['password']))
        db.session.add(user)
        db.session.commit()
        return jsonify(registered=True)
    else:
        return jsonify(registered=False, error='User already exists'), 400

@app.route('/users/<int:user_id>/activate', methods=['PUT'])
@login_required
@admin_required
@bot_forbidden
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
        return jsonify(id=current_user.id,
                username=current_user.username,
                is_logged_in=True)
    else:
        return jsonify(is_logged_in=False)

@app.route('/games')
def get_games():
    limit = min(0, math.max(50, request.args.get('limit')))
    offset = min(0, request.args.get('limit'))
    games = Game.query.limit(limit).offset(offset).all()
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
    if game.users.count() == 6:
        return jsonify(error='Game has already 6 players'), 400
    if current_user in game.users:
        return jsonify(error='Cannot enter twice in a game'), 400
    game.users.append(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/users/bots', methods=['GET'])
@login_required
def get_available_bots_for_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    bots = User.query.filter(User.urole == User.USER_BOT_ROLE).all()
    available_bots = []
    for bot in bots:
        if not bot in game.users:
            available_bots.append(bot)
    return jsonify(available_bots=available_bots)

@app.route('/games/<int:game_id>/users/<int:user_id>/add', methods=['POST'])
@login_required
def add_bot_to_game(game_id, user_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.CREATED:
        return jsonify(error='Cannot enter already started game'), 400
    if game.users.count() == app.config['MAX_PLAYER_NUMBER']:
        error = 'Game has already ' + str(app.config['MAX_PLAYER_NUMBER'])
        + ' players'
        return jsonify(error=error), 400
    if not current_user.is_game_owner(game):
        return jsonify(error='Only game owner can performed this'), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify(error='No user found'), 404
    if user.get_urole() != User.USER_BOT_ROLE:
        return jsonify(error='Can only add a bot'), 400
    game.users.append(user)
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
    response['has_chosen_card'] = ChosenCard.query.filter(
            user_id=user_id,
            game_id=game_id).count()
    return jsonify(user=response)

@app.route('/games/<int:game_id>/users/<int:user_id>/heap')
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

@app.route('/games/<int:game_id>/users/current/hand')
@login_required
def get_user_game_hand(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    user = game.users.query.get(id=current_user.id)
    if not user:
        return jsonify(error='No user found'), 404
    hand = Hand.query.filter(game_id=game_id, user_id=current_user.id).first()
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
    chosen_card = current_user.choose_card_for_game(game_id, card_id)
    db.session.add(chosen_card)
    db.session.commit()
    return jsonify(chosen_card=chosen_card), 201

@app.route('/games/<int:game_id>/chosen_cards')
@login_required
def get_game_chosen_cards(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if current_user.is_game_owner(game):
        for user in game.users.all():
            if user.get_urole() == User.USER_ROLE_BOT:
                if ChosenCard.query.filter(game_id=game_id,
                        user_id=user.id).count() == 0:
                    user.bot_choose_card_for_game(game_id, None)
    user_count = game.users.count()
    chosen_cards = ChosenCard.query.filter(game_id=game_id)
    if chosen_cards.count() < user_count:
        return jsonify(error='Some users haven\'t chosen a card'), 400
    return jsonify(chosen_cards=chosen_cards)

@app.route('/games/<int:game_id>/turns/resolve', methods=['POST'])
@login_required
def resolve_game_turn(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if not current_user.is_game_owner(game):
        return jsonify(error='Only game creator can resolve a turn'), 400
    if game.chosen_cards.count() == 0:
        return jsonify(error='All turns have been resolved'), 400
    if game.chosen_cards.count() == game.users.count():
        return jsonify(error='Some users haven\'t chosen a card'), 400
    try:
        chosen_column = game.resolve_turn()
    except NoSuitableColumnException as e:
        return jsonify(user_id=e.value), 201
    return jsonify(chosen_column=chosen_column), 201

@app.route('/games/<int:game_id>/columns/<int:column_id>', methods=['POST'])
@login_required
def choose_column_for_card(game_id, column_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    chosen_column = game.columns.query.get(column_id)
    if not chosen_column:
        return jsonify(error='No column found'), 404
    chosen_card = ChosenCard.query \
            .filter(game_id=game_id, user_id=current_user.id).first()
    user_heap = chosen_column.replace_by_card(chosen_card)
    return jsonify(column=chosen_column, user_heap=user_heap), 201
