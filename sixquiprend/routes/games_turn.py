from flask import jsonify
from flask_login import login_required, current_user
from sixquiprend.models.game import Game
from sixquiprend.sixquiprend import app

@app.route('/games/<int:game_id>/card/<int:card_id>', methods=['POST'])
@login_required
def choose_card_for_game(game_id, card_id):
    """Choose your card to play for a game"""
    game = Game.find(game_id)
    chosen_card = game.choose_card_for_user(current_user.id, card_id)
    return jsonify(chosen_card=chosen_card), 201

@app.route('/games/<int:game_id>/bots/choose_cards', methods=['POST'])
@login_required
def choose_cards_for_bots(game_id):
    """Choose cards for bots"""
    game = Game.find(game_id)
    game.choose_cards_for_bots()
    return jsonify(), 201

@app.route('/games/<int:game_id>/turns/resolve', methods=['POST'])
@login_required
def resolve_game_turn(game_id):
    """Resolve a game turn (only available to game owner). This call places the
    lowest value card if possible and returns the updated column and the user
    game heap, else returns the user_id that must choose a column to replace"""
    game = Game.find(game_id)
    [chosen_column, user_game_heap] = game.resolve_turn(current_user.id)
    return jsonify(chosen_column=chosen_column, user_heap=user_game_heap), 201

@app.route('/games/<int:game_id>/columns/<int:column_id>/choose', methods=['POST'])
@login_required
def choose_column_for_card(game_id, column_id):
    """Choose a column for your card in a game (when a user must choose a
    column to replace)"""
    game = Game.find(game_id)
    [chosen_column, user_heap] = game.choose_column_for_user(current_user.id, column_id)
    return jsonify(chosen_column=chosen_column, user_heap=user_heap), 201
