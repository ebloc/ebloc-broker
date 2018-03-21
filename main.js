var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

clusterID = "0xe056d08f050503c1f068dc81fc7f7b705fc2c503"; 

var storageType = {};
storageType['1'] = 'EUDAT';

//LOG-RECEIPT
console.log( "Cluster Gained Amount: " + eBlocBroker.getClusterReceivedAmount(clusterID))
var fs = require('fs');
var array = fs.readFileSync(nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
var titleFlag = 0;

sum=0;
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
	//str = str.replace('0x0000000000000000000000000000000000000000000000000000000000000000,', '')
	sum +=  parseInt(arr1[3]);
	console.log( "Job " + i + "\t" + arr[2] + "\t" +  arr[3] + "\t" +  storageType[arr[4]] + "\t" + arr[5] + "\t" + eBlocBroker.job_state_id[str[0]] +
		     "\t" + arr1[1] + "\t" + arr1[2]  + "\t" + arr1[3]  + "\t" + arr1[4]  + "\t" + arr1[5] );
    }
}
console.log("GAINED: " + sum)




/*
console.log(result.address + "\t" + result.args._amount / 1e16 + "\t" + result.args._from + "\t" + 
    result.args._to + "\t" + result.blockHash + "\t" + result.blockNumber + "\t" + result.event + "\t" + 
    result.logIndex + "\t" + result.transactionHash + "\t" + result.transactionIndex);
});
*/


//tx="0x5224a5a7a7a957f57ce18330b9f1b8ea50fd4746f37fcf642061a2d6ced519f3"
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
