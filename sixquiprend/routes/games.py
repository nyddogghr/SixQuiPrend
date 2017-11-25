from flask import request, jsonify
from flask_login import login_required, current_user
from sixquiprend.models.card import Card
from sixquiprend.models.chosen_card import ChosenCard
from sixquiprend.models.column import Column
from sixquiprend.models.game import Game
from sixquiprend.models.hand import Hand
from sixquiprend.models.heap import Heap
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, admin_required

@app.route('/games')
def get_games():
    """Display all games. Accepts offset and limit (up to 50)"""
    limit = max(0, min(50, int(request.args.get('limit', 50))))
    offset = max(0, int(request.args.get('offset', 0)))
    games = Game.query.order_by(Game.id).limit(limit).offset(offset).all()
    return jsonify(games=games)

@app.route('/games/count')
def count_games():
    """Count all games."""
    count = Game.query.count()
    return jsonify(count=count)

@app.route('/games/<int:game_id>')
def get_game(game_id):
    """Display a game with its results"""
    game = Game.find(game_id)
    results = game.get_results()
    return jsonify(game=game, results=results)

@app.route('/games', methods=['POST'])
@login_required
def create_game():
    """Create a new game"""
    game = Game.create(current_user)
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_game(game_id):
    """Delete a game (admin only)"""
    Game.delete(game_id)
    return '', 204

@app.route('/games/<int:game_id>/enter', methods=['POST'])
@login_required
def enter_game(game_id):
    """Enter a game (must not be started)"""
    game = Game.find(game_id)
    game.add_user(current_user)
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/users/bots', methods=['GET'])
@login_required
def get_available_bots_for_game(game_id):
    """Display available bots to add to a game"""
    game = Game.find(game_id)
    return jsonify(available_bots=game.get_available_bots())

@app.route('/games/<int:game_id>/users/<int:bot_id>/add', methods=['POST'])
@login_required
def add_bot_to_game(game_id, bot_id):
    """Add a bot to a game. Only allowed for game owner"""
    game = Game.find(game_id)
    game.add_bot(bot_id, current_user.id)
    return jsonify(game=game), 201

@app.route('/games/<int:game_id>/leave', methods=['PUT'])
@login_required
def leave_game(game_id):
    """Leave a game (nobody likes rage quitters)"""
    game = Game.find(game_id)
    game.remove_user(current_user)
    return jsonify(game=game), 200

@app.route('/games/<int:game_id>/start', methods=['PUT'])
@login_required
def start_game(game_id):
    """Start a game (only game owner can start it)"""
    game = Game.find(game_id)
    game.setup(current_user.id)
    return jsonify(game=game), 200
