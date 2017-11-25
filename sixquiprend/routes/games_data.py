from flask import session, jsonify
from flask_login import login_required, current_user
from sixquiprend.models.game import Game
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, admin_required

@app.route('/games/<int:game_id>/columns')
@login_required
def get_game_columns(game_id):
    """Get columns for the given game"""
    game = Game.find(game_id)
    return jsonify(columns=game.columns.all())

@app.route('/games/<int:game_id>/users/<int:user_id>/status')
@login_required
def get_user_game_status(game_id, user_id):
    """Get user status (has or not chosen a card) for a given game, and
    specifies if he needs to choose a column for his card"""
    game = Game.find(game_id)
    user = game.get_user_status(user_id)
    return jsonify(user=user)

@app.route('/games/<int:game_id>/users/<int:user_id>/heap')
@login_required
def get_user_game_heap(game_id, user_id):
    """Get a user's heap for a given game"""
    game = Game.find(game_id)
    heap = game.get_user_heap(user_id)
    return jsonify(heap=heap)

@app.route('/games/<int:game_id>/users/current/hand')
@login_required
def get_current_user_game_hand(game_id):
    """Get your hand for a given game"""
    game = Game.find(game_id)
    hand = game.get_user_hand(current_user.id)
    return jsonify(hand=hand)

@app.route('/games/<int:game_id>/chosen_cards')
@login_required
def get_game_chosen_cards(game_id):
    """Display chosen cards for a game. Only returns current user chosen card
    if not all users have chosen, or all chosen cards if a turn is being
    resolved"""
    game = Game.find(game_id)
    chosen_cards = game.get_chosen_cards_for_current_user(current_user.id)
    return jsonify(chosen_cards=chosen_cards)
