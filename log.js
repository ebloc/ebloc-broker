var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

readFrom  = 1807303; //eBlocBroker.getDeployedBlockNumber();
clusterID = "0x6af0204187a93710317542d383a1b547fa42e705";

eBlocBroker.LogJobResults(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt', clusterID); /* All jobs sent */

//eBlocBroker.LogReceipt(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt');


