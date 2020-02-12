var eBlocBroker = require('../contract.js');

Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

if(!web3.isConnected()){
    console.log("notconnected");
    process.exit();
}

var myContractInstance  = web3.eth.contract(eBlocBroker.abi).at(eBlocBroker.address);
fromBlock = myContractInstance.get_deployed_block_number();

var array = myContractInstance.getProviderInfo("0x6af0204187a93710317542d383a1b547fa42e705");
var eBlocBrokerEvent = myContractInstance.LogProvider({}, {fromBlock: array[0], toBlock: 'latest'});



eBlocBrokerEvent.watch( function (error, result) {
    if(result == null && flag == 0){
        fs.appendFile( myPath, "notconnected", function(err) {
            process.exit();
        });
        flag=1;
        eBlocBrokerEvent.stopWatching()
    }

    var provider = result.args.provider;
    var providerName;
    var fID;
    var miniLockId;
    var ipfsAddress;

    if (provider == "0x6af0204187a93710317542d383a1b547fa42e705") {
	providerName = result.args.providerName;
	fID         = result.args.fID;
	miniLockId  = result.args.miniLockId;
	ipfsAddress = result.args.ipfsAddress;
    }
    console.log("providerName: "        + providerName);
    console.log("fID: "                + fID);
    console.log("miniLockId: "         + miniLockId);
    console.log("ipfsAddress: "        + ipfsAddress);
    console.log("coreNumber: "         + array[1]);
    console.log("corePriceMinuteWei: " + array[2]);
    process.exit();
});
