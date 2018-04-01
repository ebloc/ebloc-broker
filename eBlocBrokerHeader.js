var nodePaths   = require('./nodePaths');
var eBlocBroker = require('./contract.js'); 

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

if(!web3.isConnected()){
    console.log("notconnected");
    process.exit();
}

web3.eth.defaultAccount = nodePaths.CLUSTER_ID; //Should be the address of the cluster.

var whoami              = web3.eth.defaultAccount;
var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);
var blockNumber         = web3.eth.blockNumber;

var gasLimit           = 4500000;
var jobBlkStart        = 0;
var job_state_id       = {};
                // = 0 #dummy do nothing
job_state_id['1']  = 'COMPLETED'
job_state_id['2']  = 'PENDING'    
job_state_id['3']  = 'RUNNING'
job_state_id['4']  = 'BOOT_FAIL';
job_state_id['5']  = 'CANCELLED'
job_state_id['6']  = 'CONFIGURING'
job_state_id['7']  = 'COMPLETING'  
job_state_id['8']  = 'FAILED'      
job_state_id['9']  = 'NODE_FAIL'
job_state_id['10'] = 'PREEMPTED'
job_state_id['11'] = 'REVOKED'    
job_state_id['12'] = 'SPECIAL_EXIT'
job_state_id['13'] = 'STOPPED'  
job_state_id['14'] = 'SUSPENDED'
job_state_id['15'] = 'TIMEOUT'    

//Global variables are used.
exports.jobBlkStart;
exports.address      = eBlocBroker.address;
exports.abi          = eBlocBroker.abi;
exports.whoami       = whoami;
exports.blockNumber  = blockNumber;
exports.job_state_id = job_state_id;

exports.getTransactionGas = function(tx) {
    return web3.eth.getTransactionReceipt( tx ).gasUsed
}

//--------------------
exports.isTransactionPassed = function(transaction_id) {
    var web3_extended = require('web3_ipc');
    var options       = { host: 'http://localhost:8545', ipc:false, personal: true,admin: true, debug: true };
    var web3          = web3_extended.create(options);
    if(!web3.isConnected()) 
	console.log("not connected");
    var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);

    var checkPassed = 0;
    var receipt     = web3.eth.getTransactionReceipt( transaction_id );

    if( (receipt != null) ) { //first it has to pass receipt check
	var status          = web3.debug.traceTransaction( transaction_id );
	//prevents for returning error message.
	//if ( status.structLogs[status.structLogs.length-1].error == "{}" )
	if( status.structLogs[status.structLogs.length-1].error == null ) { //status.structLogs[status.structLogs.length-1].error == "" )
	    //"RETURN"
	    //console.log(JSON.stringify(status.structLogs[status.structLogs.length-1]));
	    //console.log( status.structLogs[status.structLogs.length-1].error )
	    checkPassed = 1;
	}
	else{
	    //console.log(JSON.stringify(status.structLogs[status.structLogs.length-1]));
	    //console.log( status.structLogs[status.structLogs.length-1].error )
	    //---
	    //console.log(JSON.stringify(status.structLogs[status.structLogs.length-1].op));
	    //console.log(JSON.stringify(status.structLogs[status.structLogs.length-1].error));
	}
    }
    //console.log( "TransactionPassed ?= " + transaction_id + ": " + checkPassed );
    //console.log( checkPassed );
    return checkPassed;
};
//--------------------

exports.setJobStatus = function(var1, var2, var3, var4) {
    hash = myContractInstance.setJobStatus(var1, var2, var3, var4, {from: web3.eth.defaultAccount, gas: gasLimit });
    console.log( hash );
};

exports.getClusterReceivedAmount = function( var1) {
    return myContractInstance.getClusterReceivedAmount( var1 );
};

exports.getJobInfo = function(var1, var2, var3) {
    return myContractInstance.getJobInfo(var1, var2, var3);
};

exports.getSubmittedJobCore = function(var1, var2, var3) {
    return myContractInstance.getSubmittedJobCore(var1, var2, var3 );
};

exports.getJobOwner = function(var1, var2, var3) {
    return myContractInstance.getJobOwner( var1, var2, var3 );
};

exports.getClusterAddresses = function() {
    return myContractInstance.getClusterAddresses();
};

exports.updateCluster = function(var1, var2, var3, var4, var5, var6) {
    hash = myContractInstance.updateCluster( var1, var2, var3, var4, var5, var6, {from: web3.eth.defaultAccount, gas: gasLimit } );
    console.log(hash);
};

exports.getDeployedBlockNumber = function() {
    return myContractInstance.getDeployedBlockNumber();
};

exports.getClusterIpfsId = function(var1) {
    return myContractInstance.getClusterIpfsId(var1);
};

exports.isClusterExist = function(var1) {
    return myContractInstance.isClusterExist(var1);
};

exports.getClusterInfo = function(var1) {
    return myContractInstance.getClusterInfo( var1 );
};

exports.highestBlock = function() {
    var sync = web3.eth.syncing;
    console.log( sync.highestBlock );
    return sync.highestBlock;
};

exports.receiptCheck = function(var1, var2, var3, var4, var5, var6) {
    hash = myContractInstance.receiptCheck( var1, var2, var3, var4, var5, var6, {from: web3.eth.defaultAccount, gas: gasLimit} );
    console.log( hash );
};

exports.LogJob = function(var1, myPath) {
    var path  = require('path');     
    var fs    = require('fs');

    if( fs.existsSync(myPath) ) 
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.LogJob({}, {fromBlock: var1, toBlock: 'latest'});

    eBlocBrokerEvent.watch( function (error, result) {	
	flag = 0;
	if(error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if(result == null && flag == 0){
	    fs.appendFile( myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (flag == 0) {
	    var jobKey = result.args.jobKey;   

	    if (jobKey.indexOf("?") == -1  || jobKey.indexOf(" ") == -1) { 
		if (result.args.cluster == web3.eth.defaultAccount){
		    if (result.args.myMiniLockID == "")
			result.args.myMiniLockID = "-1"
		    fs.appendFile( myPath, JSON.stringify(result.blockNumber ) + " " +
				   result.args.cluster + " " +  jobKey + " " + result.args.index + " " + result.args.storageType + " " +
				   result.args.miniLockId + ' ?\n', function(err) { // '?' end of line identifier.
					   process.exit();
				   }); 	
		}
	    }
	}
    });
}

exports.LogReceipt = function(var1, myPath, clusterID) {    
    var path  = require('path');     
    var fs    = require('fs');

    if (fs.existsSync(myPath)) 
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.LogReceipt({}, {fromBlock: var1, toBlock: 'latest'});

    eBlocBrokerEvent.watch( function (error, result) {	
	flag = 0;
	if(error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (result == null && flag == 0) {
	    fs.appendFile( myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if(flag == 0){
	    var jobKey = result.args.jobKey;   
	    if (jobKey.indexOf("?") == -1  || jobKey.indexOf(" ") == -1) { 
		if(result.args.cluster == clusterID){
		    fs.appendFile(myPath, JSON.stringify(result.blockNumber) + " " +
				   result.args.cluster + " " +  jobKey + " " + result.args.index + " " + result.args.storageType + " " + result.args.endTime + " " +
				   result.args.ipfsHashOut + " " + result.args.recieved +  " " + result.args.returned + ' ?\n', function(err) { // '?' end of line identifier.
					   process.exit();
				   }); 	
		}
	    }
	}
    });
}

exports.LogJobResults = function(var1, myPath, clusterID) {
    var gain = [];
    var fs    = require('fs');

    var text = fs.readFileSync(myPath,'utf8')
    var arr = text.toString().split("\n");
    
    for (i=0; i < arr.length-1; i++) {
	var arr1 = arr[i].toString().split(" ");
	gain[arr1[0]] = arr1[1]
    }

    var path  = require('path');     

    if (fs.existsSync(myPath)) 
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.LogJob({}, {fromBlock: var1, toBlock: 'latest'});

    eBlocBrokerEvent.watch(function (error, result) {
	flag = 0;
	if(error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if(result == null && flag == 0){
	    fs.appendFile( myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (flag == 0) {
	    var jobKey = result.args.jobKey;   

	    if (jobKey.indexOf("?") == -1  || jobKey.indexOf(" ") == -1) { 
		if (result.args.cluster == clusterID){
		    if (result.args.myMiniLockID == "")
			result.args.myMiniLockID = "-1"
		    
		    myStr='';
		    if(typeof gain[result.args.cluster +  '_' + jobKey + '_' + result.args.index] === 'undefined')
			myStr='';
		    else
			myStr=gain[result.args.cluster + '_' + jobKey + '_' + result.args.index].toString();
		    
		    fs.appendFile( myPath, JSON.stringify(result.blockNumber ) + " " +
				   result.args.cluster + " " +  jobKey + " " + result.args.index + " " + result.args.storageType + " " +
				   result.args.miniLockId + " " + myStr + ' ?\n', function(err) { // '?' end of line identifier.
					   process.exit();
				   }); 	
		}
	    }
	}
    });
}

exports.saveReceipts = function(var1, myPath, clusterID) {
    var path  = require('path');     
    var fs    = require('fs');

    if (fs.existsSync(myPath)) 
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.LogReceipt({}, {fromBlock: var1, toBlock: 'latest'});

    eBlocBrokerEvent.watch( function (error, result) {	
	flag = 0;
	if(error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (result == null && flag == 0) {
	    fs.appendFile( myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if(flag == 0){
	    var jobKey = result.args.jobKey;   
	    if (jobKey.indexOf("?") == -1  || jobKey.indexOf(" ") == -1) { //not accepting any string containing '#' wrong string input affects string splitting
		if(result.args.cluster == clusterID){
		    gainedStr=(parseInt(result.args.recieved) - parseInt(result.args.returned)).toString();
		    

		    fs.appendFile(myPath, result.args.cluster + '_' + jobKey + '_' + result.args.index + ' ' + gainedStr + '\n' , function(err) { // '?' end of line identifier.			
			eBlocBrokerEvent.stopWatching();
                        process.exit();
                    });



		}
	    }
	}
    });   
}


