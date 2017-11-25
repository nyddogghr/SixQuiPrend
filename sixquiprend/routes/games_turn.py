from flask import jsonify
from flask_login import login_required, current_user
from sixquiprend.models.game import Game
from sixquiprend.sixquiprend import app

@app.route('/games/<int:game_id>/status')
@login_required
def get_game_status(game_id):
    """Get status for a game. Used to know when to choose cards
    for bots or place a card. Only available to game owner"""
    game = Game.find(game_id)
    can_place_card = game.can_place_card(current_user.id)
    can_choose_cards_for_bots = game.can_choose_cards_for_bots(current_user.id)
    is_resolving_turn = game.is_resolving_turn
    return jsonify(can_place_card=can_place_card,
            is_resolving_turn=is_resolving_turn,
            can_choose_cards_for_bots=can_choose_cards_for_bots)

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
    game.choose_cards_for_bots(current_user.id)
    return jsonify(), 201

@app.route('/games/<int:game_id>/cards/place', methods=['POST'])
@login_required
def place_game_card(game_id):
    """Tries to place a card for a game (only available to game owner). This call places the
    lowest value card if possible and returns the updated column and the user
    game heap, else returns the user_id that must choose a column to replace"""
    game = Game.find(game_id)
    [chosen_column, user_game_heap] = game.place_card(current_user.id)
    return jsonify(chosen_column=chosen_column, user_heap=user_game_heap), 201

@app.route('/games/<int:game_id>/columns/<int:column_id>/choose', methods=['POST'])
@login_required
def choose_column_for_card(game_id, column_id):
    """Choose a column for your card in a game (when a user must choose a
    column to replace)"""
    game = Game.find(game_id)
    [chosen_column, user_heap] = game.choose_column_for_user(current_user.id, column_id)
    return jsonify(chosen_column=chosen_column, user_heap=user_heap), 201
