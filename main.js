/* LOG-RECEIPT */

var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

clusterID = "0x6af0204187a93710317542d383a1b547fa42e705"; 

var storageType = {};
storageType['0'] = 'IPFS';
storageType['1'] = 'EUDAT';
storageType['2'] = 'IPFSandMiniLock';

var fs        = require('fs');
var array     = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
var titleFlag = 0;

sum = 0;
for(i in array) {
    var arr = array[i].split(" ");
    
    if (array[i] != '' && clusterID == arr[1]) {
	if (titleFlag == 0){
	    console.log("Job #\tjobKey______________________________________________________________________\tindex\tType\tStatus  \tcoreNum\tblockNum\tGained\tPrice\tcoreMinuteGas");
	    titleFlag = 1;
	}
	var str = eBlocBroker.getJobInfo(arr[1], arr[2], arr[3]).toString().split(",");
	str = str.toString();
	var arr1 = str.split(",");

	if(str[0] == '1')
	    sum +=  parseInt(arr1[3]);
	
	console.log( "Job " + i + "\t" + arr[2] + "\t" +  arr[3] + "\t" +  storageType[arr[4]] + "\t" + arr[5] + "\t" + eBlocBroker.job_state_id[str[0]] +
		     "\t" + arr1[1] + "\t" + arr1[2]  + "\t" + arr1[3]  + "\t" + arr1[4]  + "\t" + arr1[5] );
    }
}
console.log( "Cluster Gained Amount: " + sum)

//tx="0x5224a5a7a7a957f57ce18330b9f1b8ea50fd4746f37fcf642061a2d6ced519f3"
//console.log( "TransactionPassed ?= " + tx + " " + eBlocBroker.isTransactionPassed(tx) );
