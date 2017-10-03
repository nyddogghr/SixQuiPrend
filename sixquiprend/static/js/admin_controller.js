'use strict';

app.controller('AdminController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

    $scope.ui = {
      page: 1,
      limit: 25,
      user_active: 'true',
      show_users: false,
    };

    // Methods

    $scope.get_users = function() {
      $http.get('/users?active=' + $scope.ui.user_active)
      .then(function(response) {
        $scope.users = response.data.users;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
      $http.get('/users/count?active=' + $scope.ui.user_active)
      .then(function(response) {
        $scope.users.max_page = Math.ceil(response.data.count/$scope.users.limit);
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.increase_users_page = function() {
      $scope.users.page = $scope.users.page + 1;
      $scope.get_users();
    }

    $scope.decrease_users_page = function() {
      $scope.users.page = $scope.users.page - 1;
      $scope.get_users();
    }

    $scope.deactivate_user = function(user_id) {
      $http.put('/users/' + user_id + '/deactivate')
      .then(function(response) {
        $scope.get_users();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.activate_user = function(user_id) {
      $http.put('/users/' + user_id + '/activate')
      .then(function(response) {
        $scope.get_users();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Events

    $scope.$watch('ui.user_active', function() {
      $scope.get_users();
    });

  }
]);
