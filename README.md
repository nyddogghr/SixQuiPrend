# SixQuiPrend
API implementation of small card game "6 Qui Prend".

# Original Game
This implementation is based on the original game, distributed by Gigamic in
France (http://www.gigamic.com/jeu/6-qui-prend).

# Schema
* n users => n games
* 1 column => 1 game
* n column => n cards
* 1 hand => 1 user, 1 game
* n hands => n cards
* 1 heap => 1 user, 1 game
* n heaps => n cards

# Routes
* Login
* Logout
* Register user
* Get all users (if admin)
* Activate/deactivate a user (if admin)
* Delete a user
* Get all games
* Get a game result
* Delete a game
* Create a game
* Register into a game
* Leave a game
* Start a game
* Get a game's columns
* Get a game's users
* Get a player's status (choosing a card or not) for a game
* Get a player's heap for a game
* Get current player's hand
* Choose a card from current player's hand

# TODO
* Choose cards for a player
* Choose cards for the columns
* Resolve a turn (wait for all players to choose or random after timeout)
* Choose a card placement and resolve it
* incredibly smart AI that chooses randomly a card from its hand
* Count points
* Statistics
* Unit tests
* Add a validation from admin to create users (prevent spam), or anything else
