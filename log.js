var nodePaths = require('./nodePaths');
var mylib = require(nodePaths.EBLOCBROKER + '/eBlocHeader.js');

console.log( '' + mylib.getDeployedBlockNumber() )

//readFrom = mylib.getDeployedBlockNumber()
readFrom = 1382295
//mylib.LogJob( readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt' ); //COMPLETED olmayanlari print et.
mylib.LogReceipt( readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt' );
