var eBlocBroker = require('../contract.js');

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

if(!web3.isConnected()){
    console.log("notconnected");
    process.exit();
}

if (process.argv.length == 3)
    clusterAddress = process.argv[2]
else
    clusterAddress = "0x75a4c787c5c18c587b284a904165ff06a269b48c"

var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);
fromBlock = myContractInstance.getDeployedBlockNumber();

var array = myContractInstance.getClusterInfo(clusterAddress);
var eBlocBrokerEvent = myContractInstance.LogCluster({}, {fromBlock: array[0], toBlock: 'latest'});

eBlocBrokerEvent.watch( function (error, result) {
    if(result == null){
        fs.appendFile( myPath, "notconnected", function(err) {
            process.exit();
        });
        eBlocBrokerEvent.stopWatching()
    }

    var cluster = result.args.cluster;
    var clusterName;
    var fID;
    var miniLockId; 
    var ipfsAddress;
    
    if (cluster == clusterAddress) {
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

