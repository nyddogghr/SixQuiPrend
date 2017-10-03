'use strict';

app.controller('TopController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // Variables

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
        $rootScope.current_user = response.data.user;
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
        $rootScope.current_user = null;
      }, function(response) {
        growl.addErrorMessage(response.data.error);
      });
    };

  }
]);
