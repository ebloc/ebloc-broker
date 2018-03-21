var eBlocBroker = require('../contract.js');

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

if(!web3.isConnected()){
    console.log("notconnected");
    process.exit();
}

var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);
fromBlock = myContractInstance.getDeployedBlockNumber();

var array = myContractInstance.getClusterInfo("0x6af0204187a93710317542d383a1b547fa42e705");
var eBlocBrokerEvent = myContractInstance.LogCluster({}, {fromBlock: array[0], toBlock: 'latest'});



eBlocBrokerEvent.watch( function (error, result) {
    if(result == null && flag == 0){
        fs.appendFile( myPath, "notconnected", function(err) {
            process.exit();
        });
        flag=1;
        eBlocBrokerEvent.stopWatching()
    }

    var cluster = result.args.cluster;
    var clusterName;
    var fID;
    var miniLockId; 
    var ipfsAddress;
    
    if (cluster == "0x6af0204187a93710317542d383a1b547fa42e705") {
	clusterName = result.args.clusterName;
	fID         = result.args.fID;
	miniLockId  = result.args.miniLockId;
	ipfsAddress = result.args.ipfsAddress;	
    }
    console.log("clusterName: "        + clusterName);
    console.log("fID: "                + fID);
    console.log("miniLockId: "         + miniLockId);
    console.log("ipfsAddress: "        + ipfsAddress);
    console.log("coreNumber: "         + array[1]);
    console.log("corePriceMinuteWei: " + array[2]);   
    process.exit();	    
});

