var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

readFrom = 1804638; //eBlocBroker.getDeployedBlockNumber();
eBlocBroker.LogJob(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt' ); /* All jobs sent */

//eBlocBroker.LogReceipt(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt');


