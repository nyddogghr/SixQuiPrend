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
        if current_user.is_authenticated and current_user.get_urole() < User.ADMIN_ROLE:
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return func_wrapper

#############################################################
## Templates
@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/home.html')
def get_home_template():
    return render_template('home.html')

@app.route('/admin.html')
def get_admin_template():
    return render_template('admin.html')

@app.route('/game.html')
def get_game_template():
    return render_template('game.html')

#############################################################
## API
@app.route('/login', methods=['POST'])
def login():
    """Log in"""
    user = User.query \
            .filter(User.username == request.get_json()['username']).first()
    if user:
        if user.urole == User.BOT_ROLE:
            return jsonify(error='Bots cannot login'), 401
        if not user.is_active():
            return jsonify(error='User is inactive'), 403
        if user.verify_password(request.get_json()['password']):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return jsonify(status=True, user=user), 201
        else:
            return jsonify(error='Password is invalid'), 400
    else:
        return jsonify(error='User doesn\'t exist'), 404

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out"""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return jsonify(status=False), 201

@app.route('/users/register', methods=['POST'])
def register():
    if app.config['ALLOW_REGISTER_USERS'] != True:
        return jsonify(error='Registering is deactivated'), 403
    """Register a new user"""
    user = User.query \
            .filter(User.username == request.get_json()['username']).first()
    if not user:
        user = User(username=request.get_json()['username'],
                password=bcrypt.hash(request.get_json()['password']))
        db.session.add(user)
        db.session.commit()
        return jsonify(registered=True), 201
    else:
        return jsonify(error='User already exists'), 400

@app.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Display all users (admin only). Accepts offset and limit (up to 50),
    and active argument filter"""
    limit = max(0, min(50, int(request.args.get('limit', 50))))
    offset = max(0, int(request.args.get('offset', 0)))
    active = request.args.get('active')
    users = User.query
    if active != None:
        users = User.query.filter(User.active == (active != 'false'))
    users = users.order_by(User.id).limit(limit).offset(offset).all()
    return jsonify(users=users)

@app.route('/users/count', methods=['GET'])
@login_required
@admin_required
def count_users():
    """Count all users (admin only). Accepts active argument filter"""
    active = request.args.get('active')
    users = User.query
    if active != None:
        users = User.query.filter(User.active == (active != 'false'))
    count = users.count()
    return jsonify(count=count)

@app.route('/users/<int:user_id>/activate', methods=['PUT'])
@login_required
@admin_required
def activate_user(user_id):
    """Activate a user (admin only)"""
    user = User.query.get(user_id)
    if user:
        user.active = True
        db.session.add(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(error='User doesn\'t exist'), 404

@app.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@login_required
@admin_required
def deactivate_user(user_id):
    """Deactivate a user (admin only)"""
    user = User.query.get(user_id)
    if user:
        user.active = False
        db.session.add(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(error='User doesn\'t exist'), 404

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(status=True)
    else:
        return jsonify(error='User doesn\'t exist'), 404

@app.route('/users/current')
def get_current_user():
    """Get current user status"""
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        return jsonify(status=True, user=user)
    else:
        return jsonify(status=False)

@app.route('/games')
def get_games():
    """Display all games. Accepts offset and limit (up to 50)"""
    limit = max(0, min(50, int(request.args.get('limit', 50))))
    offset = max(0, int(request.args.get('offset', 0)))
    games = Game.query.order_by(Game.id).limit(limit).offset(offset).all()
    return jsonify(games=games)

@app.route('/games/count')
def countt_games():
    """Count all games."""
    count = Game.query.count()
    return jsonify(count=count)

@app.route('/games/<int:game_id>')
def get_game(game_id):
    """Display a game with its results"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    results = game.get_results()
    return jsonify(game=game, results=results)

@app.route('/games', methods=['POST'])
@login_required
def create_game():
    """Create a new game"""
    game = Game(status=Game.STATUS_CREATED)
    game.users.append(current_user)
    game.owner_id = current_user.id
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_game(game_id):
    """Delete a game (admin only)"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    db.session.delete(game)
    db.session.commit()
    return '', 204

@app.route('/games/<int:game_id>/enter', methods=['POST'])
@login_required
def enter_game(game_id):
    """Enter a game (must not be started)"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_CREATED:
        return jsonify(error='Cannot enter already started game'), 400
    if game.users.count() == app.config['MAX_PLAYER_NUMBER']:
        max_number = str(app.config['MAX_PLAYER_NUMBER'])
        error = 'Game has already ' + max_number + ' players'
        return jsonify(error=error), 400
    if current_user in game.users.all():
        return jsonify(error='Cannot enter twice in a game'), 400
    game.users.append(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/users/bots', methods=['GET'])
@login_required
def get_available_bots_for_game(game_id):
    """Display available bots to add to a game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    bots = User.query.filter(User.urole == User.BOT_ROLE).order_by(User.id).all()
    available_bots = []
    for bot in bots:
        if not bot in game.users.all():
            available_bots.append(bot)
    return jsonify(available_bots=available_bots)

@app.route('/games/<int:game_id>/users/<int:user_id>/add', methods=['POST'])
@login_required
def add_bot_to_game(game_id, user_id):
    """Add a bot to a game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_CREATED:
        return jsonify(error='Cannot add a bot to an already started game'), 400
    if game.users.count() == app.config['MAX_PLAYER_NUMBER']:
        max_number = str(app.config['MAX_PLAYER_NUMBER'])
        error = 'Game has already ' + max_number + ' players'
        return jsonify(error=error), 400
    if not current_user.is_game_owner(game):
        return jsonify(error='Only game owner can performed this'), 403
    bot = User.query.get(user_id)
    if not bot:
        return jsonify(error='No bot found'), 404
    if bot.get_urole() != User.BOT_ROLE:
        return jsonify(error='Can only add a bot'), 400
    if bot in game.users:
        return jsonify(error='Bot already present'), 400
    game.users.append(bot)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/leave', methods=['PUT'])
@login_required
def leave_game(game_id):
    """Leave a game (nobody likes rage quitters)"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if current_user not in game.users.all():
        return jsonify(error='Not in game'), 400
    if current_user.is_game_owner(game):
        try:
            game.remove_owner(current_user.id)
        except CannotRemoveOwnerException as e:
            return jsonify(error=e.args[0]), 400
    game.users.remove(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game), 200

@app.route('/games/<int:game_id>/start', methods=['PUT'])
@login_required
def start_game(game_id):
    """Start a game (only game owner can start it)"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_CREATED:
        return jsonify(error='Cannot start an already started game'), 400
    if game.users.count() < 2:
        return jsonify(error='Cannot start game with less than 2 players'), 400
    if not current_user.is_game_owner(game):
        return jsonify(error='Only game owner can start it'), 403
    game.setup_game()
    return jsonify(game=game), 200

@app.route('/games/<int:game_id>/columns')
@login_required
def get_game_columns(game_id):
    """Get columns for the given game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status == Game.STATUS_CREATED:
        return jsonify(error='Cannot display columns of an unstarted game'), 400
    columns = game.get_columns().all()
    return jsonify(columns=columns)

@app.route('/games/<int:game_id>/users')
@login_required
def get_game_users(game_id):
    """Get users for a given game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    users = game.users.all()
    return jsonify(users=users)

@app.route('/games/<int:game_id>/users/<int:user_id>/status')
@login_required
def get_user_game_status(game_id, user_id):
    """Get user status (has or not chosen a card) for a given game, and
    specifies if he needs to choose a column for his card"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status == Game.STATUS_CREATED:
        return jsonify(error='Cannot get a user\'s status of an unstarted game'), 400
    user = game.get_user(user_id)
    if not user:
        return jsonify(error='No user found'), 404
    user_response = user.serialize()
    user_response['has_chosen_card'] = user.has_chosen_card(game_id)
    user_response['needs_to_choose_column'] = user.needs_to_choose_column(game_id)
    return jsonify(user=user_response)

@app.route('/games/<int:game_id>/users/<int:user_id>/heap')
@login_required
def get_user_game_heap(game_id, user_id):
    """Get a user's heap for a given game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status == Game.STATUS_CREATED:
        return jsonify(error='Cannot get a user\'s heap of an unstarted game'), 400
    user = game.get_user(user_id)
    if not user:
        return jsonify(error='No user found'), 404
    heap = user.get_game_heap(game_id)
    return jsonify(heap=heap)

@app.route('/games/<int:game_id>/users/current/hand')
@login_required
def get_current_user_game_hand(game_id):
    """Get your hand for a given game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_STARTED:
        return jsonify(error='Can only show your hand for a started game'), 400
    user = game.get_user(current_user.id)
    if not user:
        return jsonify(error='No user found'), 404
    hand = user.get_game_hand(game_id)
    return jsonify(hand=hand)

@app.route('/games/<int:game_id>/card/<int:card_id>', methods=['POST'])
@login_required
def choose_card_for_game(game_id, card_id):
    """Choose your card to play for a game"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_STARTED:
        return jsonify(error='Can only choose a card for a started game'), 400
    user = game.get_user(current_user.id)
    if not user:
        return jsonify(error='Not in game'), 400
    if user.has_chosen_card(game_id):
        return jsonify(error='Card already chosen'), 400
    try:
        chosen_card = current_user.choose_card_for_game(game_id, card_id)
    except CardNotOwnedException:
        return jsonify(error='Cannot choose a card not owned'), 400
    return jsonify(chosen_card=chosen_card), 201

@app.route('/games/<int:game_id>/chosen_cards')
@login_required
def get_game_chosen_cards(game_id):
    """Display chosen cards for a game. Only available once all users have
    chosen"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_STARTED:
        return jsonify(error='Can only show chosen cards for a started game'), 400
    game.choose_cards_for_bots()
    user_count = game.users.count()
    chosen_cards = game.get_chosen_cards().order_by(ChosenCard.id)
    if chosen_cards.count() < user_count:
        return jsonify(error='Some users haven\'t chosen a card'), 400
    return jsonify(chosen_cards=chosen_cards.all())

@app.route('/games/<int:game_id>/turns/resolve', methods=['POST'])
@login_required
def resolve_game_turn(game_id):
    """Resolve a game turn (only available to game owner). This call places the
    lowest value card if possible and returns the updated column and the user
    game heap, else returns the user_id that must choose a column to replace"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_STARTED:
        return jsonify(error='Can only resolve a turn for a started game'), 400
    if not current_user.is_game_owner(game):
        return jsonify(error='Only game creator can resolve a turn'), 403
    if game.get_chosen_cards().count() == 0:
        return jsonify(error='No card to place'), 400
    try:
        [chosen_column, user_game_heap] = game.resolve_turn()
    except NoSuitableColumnException as e:
        return jsonify(user_id=e.args[0]), 422
    return jsonify(chosen_column=chosen_column, user_heap=user_game_heap), 201

@app.route('/games/<int:game_id>/columns/<int:column_id>/choose', methods=['POST'])
@login_required
def choose_column_for_card(game_id, column_id):
    """Choose a column for your card in a game (when a user must choose a
    column to replace)"""
    game = Game.query.get(game_id)
    if not game:
        return jsonify(error='No game found'), 404
    if game.status != Game.STATUS_STARTED:
        return jsonify(error='Can only choose a column to replace for a started game'), 400
    user = game.get_user(current_user.id)
    if not user:
        return jsonify(error='Not in game'), 400
    chosen_column = game.get_columns().filter(Column.id==column_id).first()
    if not chosen_column:
        return jsonify(error='No column found'), 404
    chosen_card = current_user.get_chosen_card(game_id)
    if not chosen_card:
        return jsonify(error='No card to place'), 400
    user_heap = chosen_column.replace_by_card(chosen_card)
    return jsonify(chosen_column=chosen_column, user_heap=user_heap), 201
