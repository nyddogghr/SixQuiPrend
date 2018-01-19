'use strict';

app.controller('MainController', ['$rootScope', '$scope', '$http', 'growl',
  function($rootScope, $scope, $http, growl) {

    // UI

    $scope.is_admin = function() {
      return $rootScope.current_user && $rootScope.current_user.urole == 2;
    };

  }
]);
