(function () {

  'use strict';

  var app = angular.module('SixQuiPrendApp', ['angular-growl']);

  app.config(['growlProvider', function(growlProvider) {
    growlProvider.globalTimeToLive(5000);
  }])

  app.controller('SixQuiPrendController', ['$scope', '$log', '$http', '$timeout', 'growl',
    function($scope, $log, $http, $timeout, growl) {

      // Variables

      $scope.ui = {
        in_game: false,
        is_logged_in: false,
        is_admin: false,
        admin: {
          user_active: 'true',
          show_users: false,
        }
      };

      $scope.user = {
        username: 'admin',
        password: 'admin'
      };

      // Methods

      // Home

      $scope.login = function(user) {
        $http.post('/login', {
          username: user.username,
          password: user.password
        })
        .then(function(response) {
          $scope.current_user = response.data.user;
          $scope.ui.is_logged_in = response.data.status;
          $scope.ui.is_admin = response.data.user.urole == 3;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.register = function(user) {
        $http.post('/users/register', {
          username: user.username,
          password: user.password
        })
        .then(function(response) {
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.logout = function() {
        $http.post('/logout')
        .then(function(response) {
          $scope.ui.is_logged_in = false;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.get_games = function() {
        $http.get('/games')
        .then(function(response) {
          $scope.games = response.data.games;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.create_game = function() {
        $http.post('/games')
        .then(function(response) {
          $scope.ui.in_game = true;
          $scope.current_game = response.data.game;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.enter_game = function(game) {
        var is_game_owner = game.owner_id == $scope.current_user.id;
        var is_already_in_game = find_by_key(game.users, $scope.current_user.id) != null;
        if (is_game_owner || is_already_in_game) {
          $scope.ui.in_game = true;
          $scope.get_game(game.id);
        } else {
          $http.post('/games/' + game.id + '/enter')
          .then(function(response) {
            $scope.ui.in_game = true;
            $scope.current_game = response.data.game;
          }, function(response) {
            growl.addErrorMessage(response.data.error);
          });
        }
      };

      // Game

      $scope.get_game = function(game_id) {
        $http.get('/games/' + game_id)
        .then(function(response) {
          $scope.current_game = response.data.game;
          if ($scope.current_game.owner_id == $scope.current_user.id
            && $scope.current_game.status == 0)
            $scope.get_available_bots_for_current_game();
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.get_available_bots_for_current_game = function() {
        $http.get('/games/' + $scope.current_game.id + '/users/bots')
        .then(function(response) {
          $scope.available_bots = response.data.available_bots;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.add_bot_to_current_game = function(bot_id) {
        $http.post('/games/' + $scope.current_game.id + '/users/' + bot_id + '/add')
        .then(function(response) {
          $scope.current_game = response.data.game;
          $scope.get_available_bots_for_current_game();
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.start_current_game = function() {
        $http.put('/games/' + $scope.current_game.id + '/start')
        .then(function(response) {
          $scope.current_game = response.data.game;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.leave_current_game = function() {
        $http.put('/games/' + $scope.current_game.id + '/leave')
        .then(function(response) {
          $scope.current_game = {};
          $scope.ui.in_game = false;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      // Admin

      $scope.get_admin_panel_users = function() {
        $http.get('/users?active=' + $scope.ui.admin.user_active)
        .then(function(response) {
          $scope.admin_panel_users = response.data.users;
          // Remove self
          remove_by_key($scope.admin_panel_users, 'id', $scope.current_user.id);
          // Remove bots
          remove_by_key($scope.admin_panel_users, 'urole', 1);
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.deactivate_user = function(user_id) {
        $http.put('/users/' + user_id + '/deactivate')
        .then(function(response) {
          $scope.get_admin_panel_users();
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.activate_user = function(user_id) {
        $http.put('/users/' + user_id + '/activate')
        .then(function(response) {
          $scope.get_admin_panel_users();
        }, function(response) {
          growl.addErrorMessage(response.data.error);
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
        if (game.status != 0)
          return false;
        if (game.users.length < 5)
          return true;
        return false;
      };

      $scope.$watch('ui.admin.user_active', function() {
        $scope.get_admin_panel_users();
      });

      // Initialisation

      // Get current user status on loading
      $http.get('/users/current')
      .then(function(response) {
        $scope.current_user = response.data.user;
        $scope.ui.is_logged_in = response.data.status;
        $scope.ui.is_admin = response.data.user.urole == 3;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
        $scope.ui.is_logged_in = false;
      });

      $scope.get_games();

    }])
}());
