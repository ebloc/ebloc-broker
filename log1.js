var nodePaths = require('./nodePaths');
var eBlocBroker     = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

if (process.argv.length == 4){
    readFrom  = parseInt(process.argv[2]);
    clusterID = process.argv[3];   
    
}
else{
    readFrom  = 1810340; 
    clusterID = "0xcc8de90b4ada1c67d68c1958617970308e4ee75e";   
}

eBlocBroker.LogJobResults(readFrom, nodePaths.LOG_PATH + '/queuedJobs.txt', clusterID); /* All jobs sent */




