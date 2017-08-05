(function () {

  'use strict';

  angular.module('SixQuiPrendApp', [])

    .controller('SixQuiPrendController', ['$scope', '$log', '$http', '$timeout',
      function($scope, $log, $http, $timeout) {

        $scope.cards = [];
        $scope.user = {
          username: 'admin',
          password: 'admin'
        };

        $scope.get_cards = function() {
          $http.get('/cards')
          .then(function(response) {
            $scope.cards = response.data.cards;
          });
        };

        $scope.login = function(user) {
          $http.post('/login', {
            username: user.username,
            password: user.password
          })
          .then(function(response) {
            $scope.is_logged_in = response.data.status;
            console.log(response);
          });
        };

        $scope.register = function(user) {
          $http.post('/register', {
            username: user.username,
            password: user.password
          })
          .then(function(response) {
            console.log(response);
          });
        };

        $scope.logout = function() {
          $http.post('/logout')
          .then(function(response) {
            $scope.is_logged_in = false;
            console.log(response);
          });
        };

        $http.get('/current_user')
        .then(function(response) {
          $scope.is_logged_in = response.data.is_logged_in;
        }, function(response) {
          $scope.is_logged_in = false;
        });


        $scope.get_cards();

      }])
}());
