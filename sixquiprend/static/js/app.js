'use strict';

var app = angular.module('SixQuiPrendApp', ['angular-growl']);

app.config(['growlProvider', function(growlProvider) {
  growlProvider.globalTimeToLive(5000);
}])
