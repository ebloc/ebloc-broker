# How to Deploy using geth-console:

'''

$ rm e.js && echo "var testOutput=`solc --optimize --combined-json abi,bin,interface e.sol`" > e.js

loadScript("e.js")
var myLinkedListLib = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:Lib"].abi))

var linkedListLib = myLinkedListLib.new({ from: eth.accounts[0], data: "0x" + testOutput.contracts["e.sol:Lib"].bin, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('Lib mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
    }
  }
);





var arrayCode = testOutput.contracts["e.sol:eBlocBroker"].bin.replace(/__e.sol:Lib__________________+/g, "be331b559af35ba6fb0df9e4fa526dbd1297d56a")
var myArray   = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:eBlocBroker"].abi));

var eBlocBroker = myArray.new({ from: eth.accounts[0], data: "0x" + arrayCode, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('eBlocBroker mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
    }
  }
);

'''