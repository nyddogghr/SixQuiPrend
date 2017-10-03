'use strict';

var app = angular.module('SixQuiPrendApp', ['angular-growl']);

app.config(['growlProvider', function(growlProvider) {
  growlProvider.globalTimeToLive(5000);
}])

app.controller('SixQuiPrendController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {


    // UI

    $scope.is_admin = function() {
      return $rootScope.current_user && $rootScope.current_user.urole == 3;
    };

    // Initialisation

    $http.get('/users/current')
    .then(function(response) {
      $rootScope.current_user = response.data.user;
    }, function(response) {
      growl.addErrorMessage(response.data.error);
      $rootScope.current_user = null;
    });

  }
]);
