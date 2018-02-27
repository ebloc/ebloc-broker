var nodePaths  = require('../nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

console.log('' + eBlocBroker.isClusterExist("0xda1e61e853bb8d63b1426295f59cb45a34425b63"));
