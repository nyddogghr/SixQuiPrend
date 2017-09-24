(function () {

  'use strict';

  angular.module('SixQuiPrendApp', [])

    .controller('SixQuiPrendController', ['$scope', '$log', '$http', '$timeout',
      function($scope, $log, $http, $timeout) {

        // Variables

        $scope.ui = {
          in_game: false,
          is_logged_in: false,
        };

        $scope.user = {
          username: 'admin',
          password: 'admin'
        };

        // Methods

        $scope.login = function(user) {
          $http.post('/login', {
            username: user.username,
            password: user.password
          })
          .then(function(response) {
            $scope.ui.is_logged_in = response.data.status;
            $scope.current_game
            $scope.show_failed_response(response);
          });
        };

        $scope.register = function(user) {
          $http.post('/users/register', {
            username: user.username,
            password: user.password
          })
          .then(function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.logout = function() {
          $http.post('/logout')
          .then(function(response) {
            $scope.ui.is_logged_in = false;
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.create_game = function() {
          $http.post('/games')
          .then(function(response) {
            $scope.ui.in_game = true;
            $scope.current_game = response.data.game;
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.enter_game = function(game) {
          if (game.owner_id == $scope.current_user.id) {
            $scope.ui.in_game = true;
            $scope.get_game(game.id);
          } else if (game.users.pluck('id').indexOf($scope.current_user.id) > -1) {
            $scope.ui.in_game = true;
            $scope.get_game(game.id);
          } else {
            $http.post('/games/' + game.id + '/enter')
            .then(function(response) {
              $scope.ui.in_game = true;
              $scope.current_game = response.data.game;
              $scope.get_available_bots_for_current_game();
            }, function(response) {
              $scope.show_failed_response(response);
            });
          }
        };

        $scope.get_game = function(game_id) {
          $http.get('/games/' + game_id)
          .then(function(response) {
            $scope.current_game = response.data.game;
            if ($scope.current_game.owner_id == $scope.current_user.id
              && $scope.current_game.status == 0)
              $scope.get_available_bots_for_current_game();
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.get_available_bots_for_current_game = function() {
          $http.get('/games/' + $scope.current_game.id + '/users/bots')
          .then(function(response) {
            $scope.available_bots = response.data.available_bots;
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.add_bot_to_current_game = function(bot_id) {
          $http.post('/games/' + $scope.current_game.id + '/users/' + bot_id + '/add')
          .then(function(response) {
            $scope.current_game = response.data.game;
            $scope.get_available_bots_for_current_game();
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.start_current_game = function() {
          $http.put('/games/' + $scope.current_game.id + '/start')
          .then(function(response) {
            $scope.current_game = response.data.game;
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        $scope.leave_current_game = function() {
          $http.put('/games/' + $scope.current_game.id + '/leave')
          .then(function(response) {
            $scope.current_game = {};
          }, function(response) {
            $scope.show_failed_response(response);
          });
        };

        // UI

        $scope.can_enter_game = function(game) {
          if (!$scope.ui.is_logged_in)
            return false;
          if ($scope.current_game && game.id == $scope.current_game.id)
            return false;
          if (game.users.pluck('id').indexOf($scope.current_user.id) > -1)
            return true;
          if (game.users.length < 5)
            return true;
          return false;
        };

        $scope.show_failed_response = function(response) {
          console.log(response);
        };

        // Initialisation

        // Get current user status on loading
        $http.get('/users/current')
        .then(function(response) {
          $scope.current_user = response.data.user;
          $scope.ui.is_logged_in = response.data.status;
        }, function(response) {
          $scope.show_failed_response(response);
          $scope.ui.is_logged_in = false;
        });

        $http.get('/games')
        .then(function(response) {
          $scope.games = response.data.games;
        }, function(response) {
          $scope.show_failed_response(response);
        });

      }])
}());
