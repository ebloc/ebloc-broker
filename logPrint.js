/* LOG-RECEIPT */

var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

if (process.argv.length == 3){
    clusterID = process.argv[2];       
}
else{
    clusterID = "0xcc8de90b4ada1c67d68c1958617970308e4ee75e";   
}

console.log(process.argv.length)
console.log('clusterID: ' + clusterID);
var storageID = {};
storageID['0'] = 'IPFS';
storageID['1'] = 'EUDAT';
storageID['2'] = 'IPFS_MiniLock';
storageID['3'] = 'GitHub';
storageID['4'] = 'GoogleDrive';

var fs        = require('fs');
var array     = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
var titleFlag = 0;

sum       = 0;
totalPaid = 0;
for (i in array) {
    var arr = array[i].split(" ");


    if (i == 102)
	break;

    if (array[i] != '' && clusterID == arr[1]) {
	if (titleFlag == 0){
	    console.log("Job #\tjobKey______________________________________________________________________\tindex\tType\tStatus  \tcoreNum\tblockNum\tRecieved\tPrice\tcoreMinuteGas\tGained");
	    titleFlag = 1;
	}
	var str = eBlocBroker.getJobInfo(arr[1], arr[2], arr[3]).toString().split(",");
	str = str.toString();
	var arr1 = str.split(",");

	//LogJob
	//if(str[0] == '1')
	//sum +=  parseInt(arr1[3]);

	//LogReceipt
	if (str[0] == '1')
	    sum += parseInt(arr[6])
	
	totalPaid += parseInt(arr1[3]);

	//break;
	console.log("Job " + i + "\t" + arr[2] + "\t" +  arr[3] + "\t" +  storageID[arr[4]] + "\t" + arr[5] + "\t" + eBlocBroker.job_state_id[str[0]] +
		     "\t" + arr1[1] + "\t" + arr1[2]  + "\t" + arr1[3]  + "\t" + arr1[4] + "\t" + arr1[5] + "\t" + arr[6]);
    }
}
console.log( "Cluster Gained Amount: " + sum);
console.log( "Total Paid: "            + totalPaid);
