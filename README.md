# SixQuiPrend [![Build Status](https://travis-ci.org/nyddogghr/SixQuiPrend.svg?branch=master)](https://travis-ci.org/nyddogghr/SixQuiPrend) [![codecov](https://codecov.io/gh/nyddogghr/SixQuiPrend/branch/master/graph/badge.svg)](https://codecov.io/gh/nyddogghr/SixQuiPrend)
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
* Register
* Get all users (if admin)
* Count all users (if admin)
* Activate/deactivate a user (if admin)
* Delete a user (if admin)
* Get current user
* Get all games
* Count all games
* Get a game (with users and points)
* Create a game
* Delete a game
* Enter a game
* Display available bots for a game (for game owner)
* Add a bot to a game (for game owner)
* Leave a game
* Start a game (initiate board and hands)
* Get a game's columns
* Get a user's status (chosen a card or not) for a game
* Get a user's heap for a game
* Get current user's hand
* Get a game's chosen cards (current user's or all users' if resolving a turn)
* Get a game status (know if owner can place a card or choose cards for bots)
* Choose a card from current user's hand
* Choose cards for bots (for game owner)
* Place a card (unless a column has to be manually chosen)
* Choose a column if needed

# TODO
* Statistics
