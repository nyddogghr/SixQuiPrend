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
* Delete a user (if admin)
* Get current user
* Get all games
* Get a game (with points)
* Create a game
* Register into a game
* Display available bots for a game
* Add a bot to a game
* Leave a game
* Start a game (initiate board and hands)
* Get a game's columns
* Get a game's users
* Get a user's status (chosen a card or not) for a game
* Get a user's heap for a game
* Get current user's hand
* Choose a card from current user's hand
* Display all users' chosen cards once all have chosen
* Resolve a turn (place cards until a column must be manually chosen)
* Choose a column if needed

# TODO
* Delete games
* Count points
* Statistics
* Unit tests
