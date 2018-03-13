var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

const args = process.argv;

var setJobStatus = "setJobStatus"
var val = args[2];

if( args[2].toString() == "setJobStatus" ){
    eBlocBroker.setJobStatus(args[3], args[4], args[5], args[6]);
}
else if( args[2].toString() == "getJobInfo" ){
    console.log('' + eBlocBroker.getJobInfo( args[3], args[4], args[5] ));
}
else if( args[2].toString() == "receiptCheck" ){
    eBlocBroker.receiptCheck(args[3], args[4], args[5], args[6], args[7], args[8]);
}
else if( args[2].toString() == "bs58_encode" ){
    eBlocBroker.bs58_encode( args[3] );
}
