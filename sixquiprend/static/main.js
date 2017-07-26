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
