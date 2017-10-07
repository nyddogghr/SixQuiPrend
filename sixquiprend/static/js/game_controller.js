'use strict';

app.controller('GameController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

    $scope.ui = {
      display_users: false
    };
    $scope.game_statuses = ['created', 'started', 'ended'];

    // Methods

    // Game info

    $scope.get_game = function(game_id) {
      $scope.current_game_user_heaps = {};
      $scope.current_game_users = {};
      $scope.current_game_user_chosen_cards = {};
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

    $scope.get_chosen_cards = function() {
      $http.get('/games/' + $scope.current_game.id + '/chosen_cards')
      .then(function(response) {
        angular.forEach(response.data.chosen_cards, function(chosen_card) {
          $scope.current_game_user_chosen_cards[chosen_card.user_id] = chosen_card.card;
        });
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.update_current_game_status = function() {
      $scope.get_current_game_columns();
      $scope.get_chosen_cards();
      angular.forEach($scope.current_game.users, function(user) {
        $scope.get_current_game_user_game_status(user.id);
        $scope.get_current_game_user_game_heap(user.id);
      });
      if ($scope.is_in_current_game())
        $scope.get_current_game_hand();
    };

    // Game actions

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
        $scope.get_game(response.data.game.id);
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

    $scope.choose_card = function(card_id) {
      $http.post('/games/' + $scope.current_game.id + '/card/' + card_id)
      .then(function(response) {
        $scope.get_current_game_user_game_status($scope.current_user.id);
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.resolve_turn = function() {
      $http.post('/games/' + $scope.current_game.id + '/turns/resolve')
      .then(function(response) {
        $scope.update_current_game_status();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Events

    $scope.$watch('current_game', function() {
      if ($scope.current_game && $scope.current_game.status > 0) {
        $scope.update_current_game_status();
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

    $scope.has_chosen_card = function(user_id) {
      return $scope.current_game_users[user_id] && $scope.current_game_users[user_id].has_chosen_card;
    };

    $scope.can_resolve_turn = function() {
      if (!$scope.is_in_current_game())
        return false;
      if (!$scope.current_game.owner_id == $rootScope.current_user.id)
        return false;
      if (!$scope.has_chosen_card($rootScope.current_user.id))
        if ($scope.current_game_user_chosen_cards.length > 0)
          return true;
        else
          return false;
      return true;
    };

  }
]);
