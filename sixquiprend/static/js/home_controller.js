'use strict';

app.controller('HomeController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

    $scope.ui = {
      page: 1,
      limit: 25
    };

    $scope.game_statuses = ['created', 'started', 'ended'];

    // Methods

    $scope.get_games = function() {
      $http.get('/games?offset=' + ($scope.ui.page - 1)* $scope.ui.limit + '&limit=' + $scope.ui.limit)
      .then(function(response) {
        $scope.games = response.data.games;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
      $http.get('/games/count')
      .then(function(response) {
        $scope.ui.max_page = Math.ceil(response.data.count/$scope.ui.limit);
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.increase_games_page = function() {
      $scope.ui.page = $scope.ui.page + 1;
      $scope.get_games();
    }

    $scope.decrease_games_page = function() {
      $scope.ui.page = $scope.ui.page - 1;
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
      var is_already_in_game = find_by_key(game.users, 'id', $rootScope.current_user.id) != null;
      if (is_already_in_game) {
        $scope.show_game(game.id);
      } else {
        $http.post('/games/' + game.id + '/enter')
        .then(function(response) {
          $scope.show_game(data.response.game.id);
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      }
    };

    $scope.show_game = function(game) {
      $rootScope.$broadcast('game_chosen', game.id);
    };

    // UI

    $scope.can_enter_game = function(game) {
      if (!$rootScope.current_user)
        return false;
      var game_is_shown = $scope.current_game && game.id == $scope.current_game.id;
      var is_already_in_game = game.users.pluck('id').indexOf($rootScope.current_user.id) > -1;
      var game_created = game.status == 0;
      var game_complete = game.users.length == 5;
      if (game_is_shown || is_already_in_game || !game_created || game_complete)
        return false;
      else
        return true;
    };

    $scope.can_show_game = function(game) {
      var game_is_shown = $scope.current_game && game.id == $scope.current_game.id;
      if (!$rootScope.current_user || game_is_shown)
        return false;
      else
        return true;
    };

    // Events

    $scope.$watch('ui.limit', function() {
      $scope.get_games();
    });
  }
]);
