var eBlocBroker = require('../contract.js');

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

if(!web3.isConnected()){
    console.log("notconnected");
    process.exit();
}

if (process.argv.length == 3)
    requesterAddress = process.argv[2]
else
    requesterAddress = "0x75a4c787c5c18c587b284a904165ff06a269b48c"

var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);

fromBlock            = myContractInstance.get_requester_info(requesterAddress);
var eBlocBrokerEvent = myContractInstance.LogRequester({}, {fromBlock: fromBlock, toBlock: fromBlock});

var fs    = require('fs');
eBlocBrokerEvent.watch( function (error, result) {
    if(result == null){
        fs.appendFile( myPath, "notconnected", function(err) {
            process.exit();
        });
        eBlocBrokerEvent.stopWatching();
    }
    
    console.log("blockReadFrom: "  + fromBlock +
		"requesterEmail: " + result.args.email +
		"miniLockID: "     + result.args.miniLockID +
		"ipfsAddress: "    + result.args.ipfsAddress +
		"fID: "            + result.args.fID)

    //eBlocBrokerEvent.stopWatching();
    //process.exit();
    
    fs.appendFile('/home/netlab/t.txt', '', function(err) { // '?' end of line identifier.
	eBlocBrokerEvent.stopWatching();
    	    process.exit();
    }); 	
});

