var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

console.log('' + eBlocBroker.getDeployedBlockNumber())

readFrom = 1799549; //eBlocBroker.getDeployedBlockNumber();

eBlocBroker.LogReceipt(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt');
//eBlocBroker.LogJob(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt' ); /* Prints jobs, which are not COMPLETED */


