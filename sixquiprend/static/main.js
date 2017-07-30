(function () {

  'use strict';

  angular.module('SixQuiPrendApp', [])

    .controller('SixQuiPrendController', ['$scope', '$log', '$http', '$timeout',
      function($scope, $log, $http, $timeout) {

        $scope.entries = [];

        $scope.get_entries = function() {
          $http.get('/entries')
          .then(function(response) {
            $scope.entries = response.data.entries;
          });
        };

        $scope.login = function() {
          $http.post('/login', {
            username: $scope.username || 'admin',
            password: $scope.password || 'admin'
          })
          .then(function(response) {
            $scope.is_logged_in = response.data.status;
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

        $scope.add_entry = function(new_entry) {
          $http.post('/add', {
            title: new_entry.title,
            text: new_entry.text
          }).then(function(response) {
            $scope.get_entries();
          });
        };

        $scope.get_entries();

      }])
}());
