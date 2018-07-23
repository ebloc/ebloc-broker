# How to Deploy using Geth Console:

## !Do this at eBloc Server!

## Terminal

```
mkdir -p ~/myContract
cp $HOME/eBlocBroker/contract/contracts/* ~/myContract
sed -i 's/\/\*emit\*\//emit/g'           ~/myContract/eBlocBroker.sol    
sed -i 's/function eBlocBroker()/constructor()/g' ~/myContract/eBlocBroker.sol
cat ~/myContract/Lib.sol > ~/myContract/e.sol && tail -n+3 ~/myContract/eBlocBroker.sol >> ~/myContract/e.sol && cd ~/myContract
rm -f ~/myContract/e.js && echo "var testOutput=`solc --optimize --combined-json abi,bin,interface e.sol`" > ~/myContract/e.js
bash ../eblocPOA/client.sh
```

### MAC
```
mkdir -p ~/myContract
cp $HOME/eBlocBroker/contract/contracts/* ~/myContract
sed -i '.original' 's/\/\*emit\*\//emit/g'           ~/myContract/eBlocBroker.sol && rm eBlocBroker.sol.original
sed -i '.original' 's/function eBlocBroker()/constructor()/g' ~/myContract/eBlocBroker.sol && rm eBlocBroker.sol.original
```
 
## Geth-Console

```

loadScript("e.js")
var myLinkedListLib = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:Lib"].abi))

var linkedListLib = myLinkedListLib.new({ from: eth.accounts[0], data: "0x" + testOutput.contracts["e.sol:Lib"].bin, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('Lib mined! address: ' + contract.address.substring(2) + ' transactionHash: ' + contract.transactionHash);

         var arrayCode = testOutput.contracts["e.sol:eBlocBroker"].bin.replace(/__e.sol:Lib__________________+/g, contract.address.substring(2) )
         var myArray   = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:eBlocBroker"].abi));

         var eBlocBroker = myArray.new({ from: eth.accounts[0], data: "0x" + arrayCode, gas: 4700000},
           function (e, contract) {
              console.log(e, contract);
              if (typeof contract.address !== 'undefined') {
                  console.log('*** eBlocBroker mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
              }
           }
        );		 
    }
  }
);

testOutput.contracts["e.sol:eBlocBroker"].abi

```
