'use strict';

app.controller('AdminController', ['$scope', '$http', 'growl',
  function($scope, $http, growl) {

    // Variables

    $scope.ui = {
      page: 1,
      limit: 25,
      user_active: 'true',
      display_users: false,
    };

    // Methods

    $scope.get_users = function() {
      $http.get('/users/count', { params: { active: $scope.ui.user_active } })
      .then(function(response) {
        $scope.ui.max_page = Math.max(1, Math.ceil(response.data.count/$scope.ui.limit));
        $scope.ui.page = Math.min($scope.ui.page, $scope.ui.max_page)
        $http.get('/users', { params: {
          active: $scope.ui.user_active,
          limit: $scope.ui.limit,
          offset: ($scope.ui.page - 1)*$scope.ui.limit
        } })
        .then(function(response) {
          $scope.users = response.data.users;
        }, function(response) {
          growl.addErrorMessage(response.data.error);
        });
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.increase_users_page = function() {
      $scope.ui.page = $scope.ui.page + 1;
      $scope.get_users();
    }

    $scope.decrease_users_page = function() {
      $scope.ui.page = $scope.ui.page - 1;
      $scope.get_users();
    }

    $scope.activate_user = function(user_id) {
      $http.put('/users/' + user_id + '/activate')
      .then(function(response) {
        $scope.get_users();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.deactivate_user = function(user_id) {
      $http.put('/users/' + user_id + '/deactivate')
      .then(function(response) {
        $scope.get_users();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    $scope.delete_user = function(user_id) {
      $http.delete('/users/' + user_id)
      .then(function(response) {
        $scope.get_users();
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

    // Events

    $scope.$watchGroup(['ui.user_active', 'ui.limit'], function() {
      $scope.get_users();
    });

  }
]);
