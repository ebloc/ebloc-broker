var nodePaths   = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');
const args      = process.argv;

if( args[2].toString() == "receiptCheck" ){
    eBlocBroker.receiptCheck(args[3], args[4], args[5], args[6], args[7], args[8]);
}

