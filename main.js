var conv = require('binstring');

var nodePaths = require('./nodePaths');
var mylib = require(nodePaths.EBLOCBROKER + '/eBlocHeader.js');

printLog = 1

//console.log( mylib.whoami );

clusterID = "0xffffffffffffffffffffffffffffffffffffffff"; //ebloc

console.log( "Existed Cluster addresses are: " + mylib.getClusterAddresses() + " | ");
console.log( "ClusterInfo: " + mylib.getClusterInfo(clusterID) );

tx="0x5224a5a7a7a957f57ce18330b9f1b8ea50fd4746f37fcf642061a2d6ced519f3"
//console.log( "TransactionPassed ?= " + tx + " " + mylib.isTransactionPassed(tx) );

//mylib.updateCluster( 4, "ebloc", "0x", "0x", 1, "0x"); 

//console.log( "Contract's deployed block number: " + mylib.getDeployedBlockNumber() );

//a = "1220" + mylib.getClusterIpfsId(clusterID).substr(2); 
//console.log( "ClusterInfo: " + mylib.getClusterInfo(clusterID) /*+ " " + mylib.bs58_decode(a)*/  );



//TEST-SIDE
/*
for(i = 2; i < 12; i++)
    mylib.setMiniLockId( "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k", i )

for(i = 2; i < 12; i++)
    console.log( "miniLockId of web3.eth.accounts[" + i + "]: " + mylib.getMiniLockId( i ) )
*/


//Create Cluster:
//      #val = os.popen('node $eblocPath/eBlocBrokerNodeCall.js bs58_encode $newHash').read().replace("\n", "").replace(" ", ""); 
//      #val = '0x' + val[4:] #remove 1220 at the beginning.
//      #logTest( "bs58_encoded: " + val )
//      #os.environ['n'] = val      



/*Latest updated contract.
ret     = '' + mylib.getClusterInfo(clusterID);
var ret = ret.toString().split(",");
console.log( conv(ret[0].substr(2), { in:'hex', out:'binary'}) )
console.log( conv(ret[1].substr(2), { in:'hex', out:'binary'}) )
console.log( conv(ret[2].substr(2), { in:'hex', out:'binary'}) )
console.log(     ret[3]                            )
console.log(     ret[4]                            )
console.log(  mylib.bs58_decode("1220" + ret[5].substr(2))     )

name       = console.log( "0x" + conv('ebloc', { in:'binary', out:'hex' }) ); 
fId        = console.log( "0x" + conv('ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu', { in:'binary', out:'hex' }) ); 
miniLockId = console.log( "0x" + conv('9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ', { in:'binary', out:'hex' }) ); 
name        = "\"" + name + "\"";
fId         = "\"" + fId + "\"";
miniLockId  = "\"" + miniLockId + "\"";
mylib.registerCluster(128, name, fId, miniLockId, 1, "QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"); 
*/

//mylib.registerCluster(4, "ebloc", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf");








//Client-Side submit:

//IPFS:
//mylib.submitJob(clusterID,"QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5", 1, "science", 10, 0, "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k" );


//EUDAT:
//mylib.submitJob(clusterID,"3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName", 1, "science", 10, 1 );


//mylib.setClusterCoreMinutePrice( clusterOwner, 10 );
//val =  mylib.getClusterInfo( clusterID )
//arr  = val.toString().split(",");
//console.log( "ClusterInfo: " + val  + " " +  arr[3]);


//LOG-RECEIPT
/*
console.log( "Cluster Gained Amount: " + mylib.getClusterReceivedAmount(clusterID)  )
var fs = require('fs');
var array = fs.readFileSync( nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
for(i in array) {
    var arr = array[i].split(" ");

    if( array[i] != '' && clusterID == arr[1] ){
	var str = mylib.getJobInfo(arr[1], arr[2], 0 ).toString().split(",");
	str = str.toString()
	str = str.replace('0x0000000000000000000000000000000000000000000000000000000000000000,', '')
	console.log( "Job " + i + ": "  + " | "+ arr[2], arr[3], arr[4], arr[5] + "|" +  mylib.job_state_id[ str[0] ] + ' ' +str);
    }
}
*/

if (printLog==1) {
    sum=0;
    sum1=0;
    console.log( "Cluster Gained Amount: " + mylib.getClusterReceivedAmount(clusterID)  )
    console.log( "Status|Core|StartTimeStamp|Recieved|CoreMinutePrice|CoreMinuteGas" )
    var fs = require('fs');
    var array = fs.readFileSync( nodePaths.LOG_PATH + '/queuedJobs.txt').toString().split("\n");
    for(i in array) {
	var arr = array[i].split(" ");

	if( array[i] != '' && clusterID == arr[1] ){
	    var str = mylib.getJobInfo(arr[1], arr[2], arr[3]).toString().split(",");
	    if(str[0] == '1'){
		sum += parseInt(str[3])
		sum1+=(parseInt(arr[7]) - parseInt(arr[8]))
	    }

	    console.log( "Job "+i+": " + mylib.job_state_id[ str[0] ] + ' ' + str[1] + " " + str[2] + " " + str[3] + " " + str[4] + " " + str[5] + " | " 
			 + arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8] );
	}
    }
    console.log("GAINED: " + sum)
    console.log("GAINED: " + sum1)
}
