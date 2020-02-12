var nodePaths   = require('./nodePaths');
var eBlocBroker = require('./contract.js');

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:" + nodePaths.RPC_PORT ));

if(!web3.eth.net.isListening().then(console.log)){ //web3@1.0.0-beta.34
    console.log("notconnected");
    process.exit();
}

web3.eth.defaultAccount = nodePaths.PROVIDER_ID; //Should be the address of the provider.

var whoami              = web3.eth.defaultAccount;
var myContractInstance  = new web3.eth.Contract(eBlocBroker.abi, eBlocBroker.address);
var blockNumber         = web3.eth.blockNumber;

var gasLimit           = 4500000;
var jobBlkStart        = 0;
var job_state_id       = {};

job_state_id['0']  = 'NULL'
job_state_id['1']  = 'COMPLETED'
job_state_id['2']  = 'REFUNDED'
job_state_id['3']  = 'PENDING'
job_state_id['4']  = 'RUNNING'
job_state_id['5']  = 'BOOT_FAIL';
job_state_id['6']  = 'CANCELLED'
job_state_id['7']  = 'CONFIGURING'
job_state_id['8']  = 'COMPLETING'
job_state_id['9']  = 'FAILED'
job_state_id['10']  = 'NODE_FAIL'
job_state_id['11'] = 'PREEMPTED'
job_state_id['12'] = 'REVOKED'
job_state_id['13'] = 'SPECIAL_EXIT'
job_state_id['14'] = 'STOPPED'
job_state_id['15'] = 'SUSPENDED'
job_state_id['16'] = 'TIMEOUT'

//Global variables are used.
exports.jobBlkStart;
exports.address      = eBlocBroker.address;
exports.abi          = eBlocBroker.abi;
exports.whoami       = whoami;
exports.blockNumber  = blockNumber;
exports.job_state_id = job_state_id;

exports.highestBlock = function() {
    var sync = web3.eth.syncing;
    console.log( sync.highestBlock );
    return sync.highestBlock;
};

exports.LogJob = function(var1, myPath) {
    var path  = require('path');
    var fs    = require('fs');
    var sleep = require('sleep');


    if (fs.existsSync(myPath))
    	fs.unlinkSync(myPath);

    var check = '[]';
    while (check == '[]') {
        myContractInstance.getPastEvents('LogJob', {
            filter: {providerAddress: [web3.eth.defaultAccount]},
            fromBlock: 1899162,
            toBlock: 'latest'
        }, function(error, event){
            check = event;
            console.log(event.address);
        })
        //sleep.sleep(15); // sleep for ten seconds
        console.log(check);
        break;
    }


    /*
	flag = 0;
	if (error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
            process.exit();
	    //eBlocBrokerEvent.stopWatching()
	}

	if (result == null && flag == 0){
	    fs.appendFile( myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag = 1;
            process.exit();
	    //eBlocBrokerEvent.stopWatching()
	}

	if (flag == 0) {
	    var jobKey = result.args.jobKey;

	    if (jobKey.indexOf("?") == -1 || jobKey.indexOf(" ") == -1) {
		if (result.args.providerAddress == web3.eth.defaultAccount){
		    fs.appendFile(myPath, JSON.stringify(result.blockNumber ) + " " +
				  result.args.providerAddress + " " +  jobKey + " " + result.args.index + " " + result.args.cloudStorageID + '\n', function(err) {
				      process.exit();
				   });
		}
	    }
	}
    });
    */
};

exports.LogCancelRefund = function(var1, myPath) {
    var path  = require('path');
    var fs    = require('fs');

    if (fs.existsSync(myPath))
    	fs.unlinkSync(myPath);

    myContractInstance.events.LogCancelRefund({
        filter: {providerAddress: [web3.eth.defaultAccount]},
        fromBlock: var1
    }, function(error, event){
        flag = 0;
	if (error) {
	    fs.appendFile(myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
            process.exit();
	}

	if (result == null && flag == 0){
	    fs.appendFile(myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag = 1;
            process.exit();
	}

	if (flag == 0) {
	    var jobKey = result.args.jobKey;
	    if (result.args.providerAddress == web3.eth.defaultAccount) {
		    fs.appendFile(myPath, JSON.stringify(result.blockNumber ) + " " +
				  result.args.providerAddress + " " + jobKey + " " + result.args.index + '\n', function(err) {
				      process.exit();
				  });
	    }

	}
    })
};


exports.LogReceipt = function(var1, myPath, providerID) {
    var path  = require('path');
    var fs    = require('fs');

    if (fs.existsSync(myPath))
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.events.LogReceipt({}, {fromBlock: var1, toBlock: 'latest'});

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
		if(result.args.providerAddress == providerID){
		    fs.appendFile(myPath, JSON.stringify(result.blockNumber) + " " +
				  result.args.providerAddress + " " +  jobKey + " " + result.args.index + " " + result.args.cloudStorageID + " " + result.args.endTime + " " +
				  result.args.ipfsHashOut + " " + result.args.recieved +  " " + result.args.returned + ' ?\n', function(err) { // '?' end of line identifier.
					  process.exit();
				  });
		}
	    }
	}
    });
};

/*
exports.LogJobResults = function(var1, myPath, providerID) {
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

    var eBlocBrokerEvent = myContractInstance.events.LogJob({}, {fromBlock: var1, toBlock: 'latest'});

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
		if (result.args.providerAddress == providerID){
		    if (result.args.myMiniLockID == "")
			result.args.myMiniLockID = "-1"

		    myStr='';
		    if(typeof gain[result.args.providerAddress +  '_' + jobKey + '_' + result.args.index] == 'undefined')
			myStr='';
		    else
			myStr=gain[result.args.providerAddress + '_' + jobKey + '_' + result.args.index].toString();

		    fs.appendFile( myPath, JSON.stringify(result.blockNumber ) + " " +
				   result.args.providerAddress + " " +  jobKey + " " + result.args.index + " " + result.args.cloudStorageID + " " +
				   result.args.miniLockId + " " + myStr + ' ?\n', function(err) { // '?' end of line identifier.
					   process.exit();
				   });
		}
	    }
	}
    });
};
*/

exports.saveReceipts = function(var1, myPath, providerID) {
    var path  = require('path');
    var fs    = require('fs');

    if (fs.existsSync(myPath))
    	fs.unlinkSync(myPath)

    var eBlocBrokerEvent = myContractInstance.events.LogReceipt({}, {fromBlock: var1, toBlock: 'latest'});

    eBlocBrokerEvent.watch(function (error, result) {
	flag = 0;
	if(error) {
	    fs.appendFile(myPath, var1 + "\n", function(err) { process.exit(); });
	    fs.appendFile(myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
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

	if(flag == 0) {
	    var jobKey = result.args.jobKey;
	    if(result.args.providerAddress == providerID){
		gainedStr=(parseInt(result.args.received) - parseInt(result.args.returned)).toString();

		fs.appendFile(myPath, result.args.providerAddress + '_' + jobKey + '_' + result.args.index + ' ' + gainedStr + '\n' , function(err) {
		    eBlocBrokerEvent.stopWatching();
                    process.exit();
                });
	    }
	}
    });
};



/* ----------------------------------------------------------------------------------------------------------------
 not used anymore
exports.getTransactionGas = function(Tx) {return web3.eth.getTransactionReceipt(Tx).gasUsed};

exports.getJobInfo = function(var1, var2, var3) {
    return myContractInstance.getJobInfo(var1, var2, var3);
};

exports.get_deployed_block_number = function() {
    return myContractInstance.get_deployed_block_number();
};

exports.getProviderIpfsId = function(var1) {
    return myContractInstance.getProviderIpfsId(var1);
};

exports.get_provider_info = function(var1) {
    return myContractInstance.get_provider_info(var1);
};

exports.get_requester_info = function(myPath, requesterAddress) {
    var fs    = require('fs');
    fromBlock            = myContractInstance.get_requester_info(requesterAddress);
    var eBlocBrokerEvent = myContractInstance.LogUser({}, {fromBlock: fromBlock, toBlock: fromBlock});
    var v = '';
    eBlocBrokerEvent.watch( function (error, result) {
	if(result == null){ eBlocBrokerEvent.stopWatching()}

	eBlocBrokerEvent.stopWatching();

	fs.writeFile(myPath, "blockReadFrom: " + fromBlock        + ',' +
		     "userEmail: "     + result.args.userEmail   + ',' +
		     "miniLockID: "    + result.args.miniLockID  + ',' +
		     "ipfsAddress: "   + result.args.ipfsAddress + ',' +
		     "fID: " + result.args.fID, function(err) {
			 process.exit();
		     });
    });
    return
};
*/

    /*
    var eBlocBrokerEvent = myContractInstance.events.LogCancelRefund({}, {fromBlock: var1, toBlock: 'latest'});
    eBlocBrokerEvent.watch(function (error, result) {
	flag = 0;
	if (error) {
	    fs.appendFile( myPath, "error related to event watch: " + error + "\n", function(err) { process.exit(); });
	    flag=1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (result == null && flag == 0){
	    fs.appendFile(myPath, "notconnected", function(err) {
		process.exit();
	    });
	    flag = 1;
	    eBlocBrokerEvent.stopWatching()
	}

	if (flag == 0) {
	    var jobKey = result.args.jobKey;
	    //if (jobKey.indexOf("?") == -1 || jobKey.indexOf(" ") == -1) {
	    if (result.args.providerAddress == web3.eth.defaultAccount) {
		    fs.appendFile(myPath, JSON.stringify(result.blockNumber ) + " " +
				  result.args.providerAddress + " " + jobKey + " " + result.args.index + '\n', function(err) {
				      process.exit();
				  });
	        }
	  //  }
	}
    });
    */

/*
exports.is_transaction_passed = function(transaction_id) {
    var web3_extended = require('web3_ipc');
    var options       = { host: 'http://localhost:' + nodePaths.RPC_PORT, ipc:false, personal: true,admin: true, debug: true };
    var web3          = web3_extended.create(options);
    if(!web3.isConnected())
	console.log("not connected");
    var myContractInstance  = new web3.eth.Contract(eBlocBroker.abi).at(eBlocBroker.address);

    var checkPassed = 0;
    var receipt     = web3.eth.getTransactionReceipt(transaction_id);

    if( (receipt != null) ) { //first it has to pass receipt check
	var status          = web3.debug.traceTransaction(transaction_id);
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
*/
