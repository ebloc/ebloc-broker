# How to Deploy using geth-console:

## Console

'''
dir='/Users/alper/DENE/eBlocBroker/contract/contracts'
cat $dir/Lib.sol > ~/e.sol && tail -n+3 $dir/eBlocBroker.sol >> ~/e.sol
rm e.js && echo "var testOutput=`solc --optimize --combined-json abi,bin,interface e.sol`" > e.js
'''

## geth-Console

'''
loadScript("e.js")
var myLinkedListLib = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:Lib"].abi))

var linkedListLib = myLinkedListLib.new({ from: eth.accounts[0], data: "0x" + testOutput.contracts["e.sol:Lib"].bin, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('Lib mined! address: ' + contract.address.substring(2) + ' transactionHash: ' + contract.transactionHash);
    }
  }
);






var arrayCode = testOutput.contracts["e.sol:eBlocBroker"].bin.replace(/__e.sol:Lib__________________+/g, "05b63d110b79a00986f962d36fe0501905d04ac5")
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
