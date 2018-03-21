var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

readFrom = 1805917; //eBlocBroker.getDeployedBlockNumber();
clusterID = "0xe056d08f050503c1f068dc81fc7f7b705fc2c503";

eBlocBroker.LogJob(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt', clusterID); /* All jobs sent */

//eBlocBroker.LogReceipt(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt');


