'use strict'

angular.module('notificationApp', ['ngRoute'])
    .config(function($routeProvider, $locationProvider) {
        $routeProvider
        .when('/notifications/:notification_id', {
            controller: 'NotificationController',
            templateUrl: '/vms.html',
        })
    })
    .controller('NotificationController', function($scope, $http, $routeParams) {
        $scope.vms = [];
        var updateVMs = function() {
            $http.get('/api/notifications/' + $routeParams.notification_id)
                .success(function(data, status, headers, config) {
                    $scope.vms = data.vms;
                    console.log($scope.vms);
                })
                .error(function(data, status, headers, config) {
                });
        };
        updateVMs();
        $scope.ack = function(vm_id) {
            $http.put('/api/vms/' + vm_id)
                .success(function(data, status, headers, config) {
                    updateVMs();
                })
                .error(function(data, status, headers, config) {
                    console.log(status + ": " + data);
                });

        };
        });
