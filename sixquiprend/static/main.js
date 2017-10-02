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
        games: {
          page: 1,
          limit: 25
        },
        users: {
          page: 1,
          limit: 25
        },
        admin: {
          user_active: 'true',
          show_users: false,
        }
      };

      $scope.game_statuses = ['created', 'started', 'ended'];

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
          $scope.current_user = null;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.get_games = function() {
        $http.get('/games?offset=' + ($scope.ui.games.page - 1)* $scope.ui.games.limit + '&limit=' + $scope.ui.games.limit)
        .then(function(response) {
          $scope.games = response.data.games;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
        $http.get('/games/count')
        .then(function(response) {
          $scope.ui.games.max_page = Math.ceil(response.data.count/$scope.ui.games.limit);
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.increase_games_page = function() {
        $scope.ui.games.page = $scope.ui.games.page + 1;
        $scope.get_games();
      }

      $scope.decrease_games_page = function() {
        $scope.ui.games.page = $scope.ui.games.page - 1;
        $scope.get_games();
      }

      $scope.create_game = function() {
        $http.post('/games')
        .then(function(response) {
          $scope.current_game = response.data.game;
          $scope.get_games();
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.enter_game = function(game) {
        var is_already_in_game = find_by_key(game.users, 'id', $scope.current_user.id) != null;
        if (is_already_in_game) {
          $scope.get_game(game.id);
        } else {
          $http.post('/games/' + game.id + '/enter')
          .then(function(response) {
            $scope.current_game = response.data.game;
          }, function(response) {
            growl.addErrorMessage(response.data.error);
          });
        }
      };

      $scope.show_game = function(game) {
        $scope.get_game(game.id);
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
        if (find_by_key($scope.current_game.users, 'id', $scope.current_user.id) == null) {
          $scope.current_game = null;
        } else {
          $http.put('/games/' + $scope.current_game.id + '/leave')
          .then(function(response) {
            $scope.current_game = null;
          }, function(response) {
            growl.addErrorMessage(response.data.error);
          });
        }
      };

      // Admin

      $scope.get_admin_panel_users = function() {
        $http.get('/users?active=' + $scope.ui.admin.user_active)
        .then(function(response) {
          $scope.admin_panel_users = response.data.users;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
        $http.get('/users/count?active=' + $scope.ui.admin.user_active)
        .then(function(response) {
          $scope.ui.users.max_page = Math.ceil(response.data.count/$scope.ui.users.limit);
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      };

      $scope.increase_users_page = function() {
        $scope.ui.users.page = $scope.ui.users.page + 1;
        $scope.get_admin_panel_users();
      }

      $scope.decrease_users_page = function() {
        $scope.ui.users.page = $scope.ui.users.page - 1;
        $scope.get_admin_panel_users();
      }

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

      $scope.is_in_current_game = function() {
        return $scope.current_user && $scope.current_game &&
          find_by_key($scope.current_game.users, 'id', $scope.current_user.id) != null;
      };

      $scope.can_enter_game = function(game) {
        var game_is_shown = $scope.current_game && game.id == $scope.current_game.id;
        var is_already_in_game = game.users.pluck('id').indexOf($scope.current_user.id) > -1;
        var game_created = game.status == 0;
        var game_complete = game.users.length == 5;
        if (!$scope.current_user || game_is_shown || is_already_in_game || !game_created || game_complete)
          return false;
        else
          return true;
      };

      $scope.can_show_game = function(game) {
        var game_is_shown = $scope.current_game && game.id == $scope.current_game.id;
        if (!$scope.current_user || game_is_shown)
          return false;
        else
          return true;
      };

      $scope.is_admin = function() {
        return $scope.current_user && $scope.current_user.urole == 3;
      };

      // Events

      $scope.$watch('ui.admin.user_active', function() {
        $scope.get_admin_panel_users();
      });

      $scope.$watch('ui.games.limit', function() {
        $scope.get_games();
      });

      // Initialisation

      $http.get('/users/current')
      .then(function(response) {
        $scope.current_user = response.data.user;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
        $scope.current_user = null;
      });

      $scope.get_games();

    }])
}());
