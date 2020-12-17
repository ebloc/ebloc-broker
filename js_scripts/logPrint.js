/* LOG-RECEIPT */

var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

if (process.argv.length == 3){
    providerID = process.argv[2];
}
else{
    providerID = "0x4e4a0750350796164D8DefC442a712B7557BF282";
}

console.log(process.argv.length)
console.log('providerID: ' + providerID);
var cloudStorageID = {};
cloudStorageID['0'] = 'IPFS';
cloudStorageID['1'] = 'EUDAT';
cloudStorageID['2'] = 'IPFS_MiniLock';
cloudStorageID['3'] = 'GitHub';
cloudStorageID['4'] = 'GoogleDrive';

var fs        = require('fs');
var array     = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
var titleFlag = 0;

sum       = 0;
totalPaid = 0;
for (i in array) {
    var arr = array[i].split(" ");

    // if (i == 102) break;
    if (array[i] != '' && providerID == arr[1]) {
	if (titleFlag == 0){
	    console.log("Job #\tjobKey______________________________________________________________________\tindex\tType\tStatus  \tcoreNum\tblockNum\tRecieved\tPrice\tcoreMinuteGas\tGained");
	    titleFlag = 1;
	}
	var str = eBlocBroker.getJobInfo(arr[1], arr[2], arr[3]).toString().split(",");
	str = str.toString();
	var arr1 = str.split(",");

	//LogReceipt
	if (str[0] == '1')
	    sum += parseInt(arr[6])

	totalPaid += parseInt(arr1[3]);

	//break;
	console.log("Job " + i + "\t" + arr[2] + "\t" +  arr[3] + "\t" +  cloudStorageID[arr[4]] + "\t" + /*arr[5] + "\t" +*/ eBlocBroker.job_state_id[str[0]].padStart(10) +
		    "\t" + arr1[1] + "\t" + arr1[2]  + "\t" + arr1[3]  + "\t" + arr1[4] + "\t" + arr1[5] + "\t" + arr[6]);
    }
}
console.log( "Provider Gained Amount: " + sum);
console.log( "Total Paid: "            + totalPaid);
