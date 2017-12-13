'use strict';

app.controller('GameController', ['$rootScope', '$scope', '$http', '$interval', 'growl',
  function($rootScope, $scope, $http, $interval, growl) {

    // Variables

    $scope.ui = {
      display_users: true,
      display_heap: {}
    };
    $scope.game_statuses = ['created', 'started', 'ended'];
    $scope.user_roles = ['bot', 'user', 'admin'];

    // Methods

    // Game info

    $scope.get_game = function() {
      $http.get('/games/' + $scope.game_id)
      .then(function(response) {
        $scope.current_game = response.data.game;
        $rootScope.is_in_game = true;
        $scope.is_resolving_turn = $scope.current_game.is_resolving_turn;
        switch($scope.current_game.status) {
          case $scope.game_statuses.indexOf('created'):
            if ($scope.current_game.owner_id == $rootScope.current_user.id)
              $scope.get_available_bots();
            break;
          case $scope.game_statuses.indexOf('started'):
            $scope.get_columns();
            angular.forEach($scope.current_game.users, function(user) {
              $scope.get_user_status(user.id);
              $scope.get_user_heap(user.id);
            });
            if ($scope.is_resolving_turn)
              $scope.get_chosen_cards();
            if ($scope.is_in_current_game()) {
              $scope.get_current_user_hand();
            }
            break;
          case $scope.game_statuses.indexOf('ended'):
            angular.forEach($scope.current_game.users, function(user) {
              $scope.ui.display_heap[user.id] = false;
              $scope.get_user_heap(user.id);
            });
            break;
        }
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_game_status = function() {
      $http.get('/games/' + $scope.game_id + '/status')
      .then(function(response) {
        $scope.can_place_card = response.data.can_place_card;
        $scope.can_choose_cards_for_bots = response.data.can_choose_cards_for_bots;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_available_bots = function() {
      $http.get('/games/' + $scope.current_game.id + '/users/bots')
      .then(function(response) {
        $scope.available_bots = response.data.available_bots;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_columns = function() {
      $http.get('/games/' + $scope.current_game.id + '/columns')
      .then(function(response) {
        $scope.columns = response.data.columns;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_user_status = function(user_id) {
      $http.get('/games/' + $scope.current_game.id + '/users/' + user_id + '/status')
      .then(function(response) {
        $scope.users[user_id] = response.data.user;
        if (user_id == $rootScope.current_user.id && response.data.user.has_chosen_card)
          $scope.get_chosen_cards();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_user_heap = function(user_id) {
      $http.get('/games/' + $scope.current_game.id + '/users/' + user_id + '/heap')
      .then(function(response) {
        $scope.user_heaps[user_id] = response.data.heap.cards;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_current_user_hand = function() {
      $http.get('/games/' + $scope.current_game.id + '/users/current/hand')
      .then(function(response) {
        $scope.hand = response.data.hand;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.get_chosen_cards = function() {
      $http.get('/games/' + $scope.current_game.id + '/chosen_cards')
      .then(function(response) {
        angular.forEach(response.data.chosen_cards, function(chosen_card) {
          $scope.user_chosen_cards[chosen_card.user_id] = chosen_card.card;
        });
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Game actions

    $scope.add_bot = function(bot_id) {
      $http.post('/games/' + $scope.current_game.id + '/users/' + bot_id + '/add')
      .then(function(response) {
        $scope.current_game = response.data.game;
        $scope.get_available_bots();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.leave_game = function() {
      if (find_by_key($scope.current_game.users, 'id', $rootScope.current_user.id) == null) {
        $scope.current_game = null;
        $rootScope.is_in_game = false;
      } else {
        $http.put('/games/' + $scope.current_game.id + '/leave')
        .then(function(response) {
          $scope.current_game = null;
          $rootScope.is_in_game = false;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      }
    };

    $scope.start_game = function() {
      $http.put('/games/' + $scope.current_game.id + '/start')
      .then(function(response) {
        $scope.get_game();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.hide_game = function() {
      $scope.current_game = null;
      $rootScope.is_in_game = false;
    };

    $scope.choose_card = function(card_id) {
      $http.post('/games/' + $scope.current_game.id + '/card/' + card_id)
      .then(function(response) {
        $scope.get_user_status($scope.current_user.id);
        $scope.get_chosen_cards();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.choose_cards_for_bots = function() {
      $http.post('/games/' + $scope.current_game.id + '/bots/choose_cards')
      .then(function(response) {
        $scope.get_game();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.place_card = function() {
      $http.post('/games/' + $scope.current_game.id + '/cards/place')
      .then(function(response) {
        $scope.get_game();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.choose_column = function(column_id) {
      $http.post('/games/' + $scope.current_game.id + '/columns/' + column_id + '/choose')
      .then(function(response) {
        $scope.get_game();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // UI

    $scope.is_in_current_game = function() {
      return $rootScope.current_user && $scope.current_game &&
        find_by_key($scope.current_game.users, 'id', $rootScope.current_user.id) != null;
    };

    $scope.get_heap_sum = function(user_id) {
      var user_heap = $scope.user_heaps[user_id];
      if (!user_heap)
        return 0;
      else
        return sum_values(user_heap, 'cow_value');
    };

    $scope.toggle_display_heap = function(user_id) {
      $scope.ui.display_heap[user_id] = !$scope.ui.display_heap[user_id];
    }

    $scope.has_chosen_card = function(user_id) {
      return $scope.users[user_id] && $scope.users[user_id].has_chosen_card;
    };

    $scope.needs_to_choose_column = function(user_id) {
      return $scope.users[user_id] && $scope.users[user_id].needs_to_choose_column;
    };

    // Events

    $scope.$on('game_chosen', function(event, game_id) {
      $scope.game_id = game_id;
      $scope.user_heaps = {};
      $scope.users = {};
      $scope.user_chosen_cards = {};
      $scope.get_game();
    });

    $interval(function() {
      if ($scope.current_game &&
        $scope.current_game.owner_id == $rootScope.current_user.id &&
        $scope.game_statuses.indexOf('started') == $scope.current_game.status)
        $scope.get_game_status();
    }, 2000);

    $interval(function() {
      if ($scope.current_game && $scope.current_game.status < 2)
        $scope.get_game();
    }, 2000);
  }
]);
