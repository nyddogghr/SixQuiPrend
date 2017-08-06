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
    return jsonify(games=[g.serialize() for g in games])

@app.route('/games', methods=['POST'])
@login_required
def create_game():
    game = Game()
    game.users.append(current_user)
    db.session.add(game)
    db.session.commit()
    return jsonify(game=game.serialize())
