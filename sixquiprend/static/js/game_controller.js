'use strict';

app.controller('GameController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

    $scope.game_statuses = ['created', 'started', 'ended'];

    // Methods

    $scope.get_game = function(game_id) {
      $http.get('/games/' + game_id)
      .then(function(response) {
        $rootScope.current_game = response.data.game;
        if ($rootScope.current_game.owner_id == $rootScope.current_user.id
          && $rootScope.current_game.status == 0)
          $scope.get_available_bots_for_current_game();
        $rootScope.current_game_users = [];
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_available_bots_for_current_game = function() {
      $http.get('/games/' + $rootScope.current_game.id + '/users/bots')
      .then(function(response) {
        $scope.available_bots = response.data.available_bots;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.add_bot_to_current_game = function(bot_id) {
      $http.post('/games/' + $rootScope.current_game.id + '/users/' + bot_id + '/add')
      .then(function(response) {
        $rootScope.current_game = response.data.game;
        $scope.get_available_bots_for_current_game();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.start_current_game = function() {
      $http.put('/games/' + $rootScope.current_game.id + '/start')
      .then(function(response) {
        $rootScope.current_game = response.data.game;
        $scope.get_games();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.leave_current_game = function() {
      if (find_by_key($rootScope.current_game.users, 'id', $rootScope.current_user.id) == null) {
        $rootScope.current_game = null;
      } else {
        $http.put('/games/' + $rootScope.current_game.id + '/leave')
        .then(function(response) {
          $rootScope.current_game = null;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      }
    };

    $scope.get_current_game_columns = function() {
      $http.get('/games/' + $rootScope.current_game.id + '/columns')
      .then(function(response) {
        $rootScope.current_game_columns = response.data.columns;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_user_game_status = function(user_id) {
      $http.get('/games/' + ŝcope.current_game.id + '/users/' + user_id + '/status')
      .then(function(response) {
        $rootScope.current_game_users[user_id] = response.data.user;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_user_game_heap = function(user_id) {
      $http.get('/games/' + $rootScope.current_game.id + '/users/' + user_id + '/heap')
      .then(function(response) {
        $rootScope.current_game_user_heaps[user_id] = response.data.heap;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_hand = function() {
      $http.get('/games/' + $rootScope.current_game.id + '/users/current/hand')
      .then(function(response) {
        $rootScope.current_game_user_hand = response.data.hand;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Events

    $scope.$watch('current_game', function() {
      if ($rootScope.current_game && $rootScope.current_game.status > 0) {
        $scope.get_current_game_columns();
        if ($scope.is_in_current_game())
          $scope.get_current_game_hand();
      }
    });

    $scope.$on('game_chosen', function(event, game_id) {
      $scope.get_game(game_id);
    });

    // UI

    $scope.is_in_current_game = function() {
      return $rootScope.current_user && $rootScope.current_game &&
        find_by_key($rootScope.current_game.users, 'id', $rootScope.current_user.id) != null;
    };

  }
]);
