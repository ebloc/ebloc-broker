var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

if (process.argv.length == 4){
    readFrom  = parseInt(process.argv[2]);
    providerID = process.argv[3];   
    
}
else{
    readFrom  = 1810340; 
    providerID = "0xcc8de90b4ada1c67d68c1958617970308e4ee75e";   
}

eBlocBroker.saveReceipts(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt', providerID);
