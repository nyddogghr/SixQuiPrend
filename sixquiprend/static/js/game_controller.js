'use strict';

app.controller('GameController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

    $scope.ui = {
      display_users: false
    };
    $scope.game_statuses = ['created', 'started', 'ended'];
    $scope.current_game_user_heaps = {};
    $scope.current_game_users = {};

    // Methods

    $scope.get_game = function(game_id) {
      $http.get('/games/' + game_id)
      .then(function(response) {
        $scope.current_game = response.data.game;
        $rootScope.is_in_game = true;
        if ($scope.current_game.owner_id == $rootScope.current_user.id
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
        $scope.get_games();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.leave_current_game = function() {
      if (find_by_key($scope.current_game.users, 'id', $rootScope.current_user.id) == null) {
        $scope.current_game = null;
        $rootScope.is_in_game = false;
      } else {
        $http.put('/games/' + $scope.current_game.id + '/leave')
        .then(function(response) {
          $scope.current_game = null;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      }
    };

    $scope.hide_current_game = function() {
      $scope.current_game = null;
      $rootScope.is_in_game = false;
    };

    $scope.get_current_game_columns = function() {
      $http.get('/games/' + $scope.current_game.id + '/columns')
      .then(function(response) {
        $scope.current_game_columns = response.data.columns;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_hand = function() {
      $http.get('/games/' + $scope.current_game.id + '/users/current/hand')
      .then(function(response) {
        $scope.current_game_user_hand = response.data.hand;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_user_game_status = function(user_id) {
      $http.get('/games/' + $scope.current_game.id + '/users/' + user_id + '/status')
      .then(function(response) {
        $scope.current_game_users[user_id] = response.data.user;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_game_user_game_heap = function(user_id) {
      $http.get('/games/' + $scope.current_game.id + '/users/' + user_id + '/heap')
      .then(function(response) {
        $scope.current_game_user_heaps[user_id] = response.data.heap.cards;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Events

    $scope.$watch('current_game', function() {
      if ($scope.current_game && $scope.current_game.status > 0) {
        $scope.get_current_game_columns();
        angular.forEach($scope.current_game.users, function(user) {
          $scope.get_current_game_user_game_status(user.id);
          $scope.get_current_game_user_game_heap(user.id);
        });
        if ($scope.is_in_current_game())
          $scope.get_current_game_hand();
      }
    });

    $scope.$on('game_chosen', function(event, game_id) {
      $scope.get_game(game_id);
    });

    // UI

    $scope.is_in_current_game = function() {
      return $rootScope.current_user && $scope.current_game &&
        find_by_key($scope.current_game.users, 'id', $rootScope.current_user.id) != null;
    };

    $scope.get_heap_sum = function(user_id) {
      var user_heap = $scope.current_game_user_heaps[user_id];
      if (!user_heap)
        return 0;
      else
        return sum_values(user_heap, 'cow_value');
    };

  }
]);
