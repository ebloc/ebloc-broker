var conv = require('binstring');

var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

printLog = 1

clusterID = "0x6af0204187a93710317542d383a1b547fa42e705"; 

tx="0x5224a5a7a7a957f57ce18330b9f1b8ea50fd4746f37fcf642061a2d6ced519f3"
//console.log( "TransactionPassed ?= " + tx + " " + eBlocBroker.isTransactionPassed(tx) );

//eBlocBroker.updateCluster( 4, "ebloc", "0x", "0x", 1, "0x"); 

//console.log( "Contract's deployed block number: " + eBlocBroker.getDeployedBlockNumber() );

//a = "1220" + eBlocBroker.getClusterIpfsId(clusterID).substr(2); 
//console.log( "ClusterInfo: " + eBlocBroker.getClusterInfo(clusterID) /*+ " " + eBlocBroker.bs58_decode(a)*/  );

//TEST-SIDE
/*
for(i = 2; i < 12; i++)
    eBlocBroker.setMiniLockId( "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k", i )

for(i = 2; i < 12; i++)
    console.log( "miniLockId of web3.eth.accounts[" + i + "]: " + eBlocBroker.getMiniLockId( i ) )
*/



//LOG-RECEIPT
console.log( "Cluster Gained Amount: " + eBlocBroker.getClusterReceivedAmount(clusterID))
var fs = require('fs');
var array = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
for(i in array) {
    var arr = array[i].split(" ");
    if( array[i] != '' && clusterID == arr[1] ){
	var str = eBlocBroker.getJobInfo(arr[1], arr[2], 0).toString().split(",");
	str = str.toString()
	//str = str.replace('0x0000000000000000000000000000000000000000000000000000000000000000,', '')
	console.log( "Job " + i + ": "  + " | "+ arr[2], arr[3], arr[4], arr[5] + "|" +  eBlocBroker.job_state_id[str[0]] + ' ' +str);
    }
}


/*
if (printLog==1) {
    sum=0;
    sum1=0;
    console.log( "Cluster Gained Amount: " + eBlocBroker.getClusterReceivedAmount(clusterID)  )
    console.log( "Status|Core|StartTimeStamp|Recieved|CoreMinutePrice|CoreMinuteGas" )
    var fs = require('fs');
    var array = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
    for(i in array) {
	var arr = array[i].split(" ");

	if( array[i] != '' && clusterID == arr[1] ){
	    var str = eBlocBroker.getJobInfo(arr[1], arr[2], arr[3]).toString().split(",");
	    if(str[0] == '1'){
		sum += parseInt(str[3])
		sum1+=(parseInt(arr[7]) - parseInt(arr[8]))
	    }

	    console.log( "Job "+ i +": " + eBlocBroker.job_state_id[str[0]] + ' ' + str[1] + " " + str[2] + " " + str[3] + " " + str[4] + " " + str[5] + " | " 
			 + arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8] );
	}
    }
    console.log("GAINED: " + sum)
    console.log("GAINED: " + sum1)
}
*/
