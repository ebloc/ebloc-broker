var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

console.log(nodePaths.EBLOCBROKER)
if (process.argv.length == 4){
    readFrom  = parseInt(process.argv[2]);
    providerID = process.argv[3];       
}
else{
    readFrom  = 2150498; 
    providerID = "0x4e4a0750350796164D8DefC442a712B7557BF282";   
}

/* All jobs are stored in queuedJobs.txt */
eBlocBroker.LogJobResults(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt', providerID); 
