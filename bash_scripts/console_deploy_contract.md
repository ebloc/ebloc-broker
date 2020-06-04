# How to Deploy using Geth Console:

## !!!!! DO THIS AT eBloc SERVER !!!!!

## Terminal

### Mac

```bash
cd ~/eBlocBroker
git fetch
git checkout origin/master -- contract/contracts/eBlocBroker.sol
git checkout origin/master -- contract/contracts/Lib.sol
mkdir -p $HOME/myContract
cp $HOME/eBlocBroker/contract/contracts/* $HOME/myContract
sed -i '.original' 's/\/\*emit\*\//emit/g'            $HOME/myContract/eBlocBroker.sol
sed -i '.original' 's/function eBlocBroker()/constructor()/g' $HOME/myContract/eBlocBroker.sol
cat $HOME/myContract/eBlocBroker.sol > $HOME/myContract/e.sol
echo "" >> $HOME/myContract/e.sol
tail -n+9 $HOME/myContract/Lib.sol >> $HOME/myContract/e.sol
sed -i 's/\^0.4.17/\^0.4.24/g' $HOME/myContract/e.sol
sed -i 's/import \".\/Lib.sol\";//g' $HOME/myContract/e.sol
cp $HOME/myContract/e.sol $HOME/eBlocBroker/deployedContract/eBlocBroker.sol
cd $HOME/myContract
rm -f $HOME/myContract/e.js
echo "var testOutput=`solc --optimize --combined-json abi,bin,interface e.sol`" > $HOME/myContract/e.js
```

----------------------------------------------------------------------------------------------

### Linux

```bash
cd $HOME/eBlocBroker
rm .git/index.lock
git fetch
git checkout origin/master -- contract/contracts/eBlocBroker.sol
git checkout origin/master -- contract/contracts/eBlocBrokerInterface.sol
git checkout origin/master -- contract/contracts/Lib.sol
mkdir -p $HOME/myContract
cp $HOME/eBlocBroker/contract/contracts/* $HOME/myContract
sed -i 's/\/\*emit\*\//emit/g'            $HOME/myContract/eBlocBroker.sol
sed -i 's/\/\*payable\*\//payable/g'            $HOME/myContract/eBlocBroker.sol
sed -i 's/\/\*payable\*\//payable/g'            $HOME/myContract/Lib.sol
sed -i 's/function eBlocBroker()/constructor()/g' $HOME/myContract/eBlocBroker.sol
head -7    $HOME/myContract/eBlocBroker.sol > $HOME/myContract/e.sol
tail -n+3  $HOME/myContract/eBlocBrokerInterface.sol >> $HOME/myContract/e.sol
echo "" >> $HOME/myContract/e.sol
tail -n+11 $HOME/myContract/eBlocBroker.sol >> $HOME/myContract/e.sol
echo "" >> $HOME/myContract/e.sol
tail -n+9  $HOME/myContract/Lib.sol >> $HOME/myContract/e.sol
sed -i 's/\^0.4.17/\^0.5.2/g' $HOME/myContract/e.sol
sed -i 's/import \".\/Lib.sol\";//g' $HOME/myContract/e.sol
sed -i 's/import \".\/eBlocBrokerInterface.sol\";//g' $HOME/myContract/e.sol
cp $HOME/myContract/e.sol $HOME/eBlocBroker/deployedContract/eBlocBroker.sol
cd $HOME/myContract
rm -f $HOME/myContract/e.js
echo "var testOutput=`solc --optimize --combined-json abi,bin,interface e.sol`" > $HOME/myContract/e.js
```

### Geth-Console

# Open geth-console

```bash
cd $HOME/myContract
bash $HOME/eBlocPOA/client.sh
```

#### v0.5.x -----------------------------------------------------------------------------------------------

```bash
loadScript("e.js")
var myLinkedListLib = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:Lib"].abi))
var linkedListLib = myLinkedListLib.new({from: eth.accounts[0], data: "0x" + testOutput.contracts["e.sol:Lib"].bin, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('Lib mined! address: ' + contract.address.substring(2) + ' transactionHash: ' + contract.transactionHash);

         var arrayCode = testOutput.contracts["e.sol:eBlocBroker"].bin.replace(/__\$e6336c56514d5fcaf1e838570aebaf012d\$__+/g, contract.address.substring(2))
         var myArray   = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:eBlocBroker"].abi));

	     console.log('Submittin eBlocBroker...');
		 arrayCode = "0x" + arrayCode;
         var eBlocBroker = myArray.new({from: eth.accounts[0], data: arrayCode, gas: 8100000},
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

#### v0.4.25 -----------------------------------------------------------------------------------------------

```bash
loadScript("e.js")
var myLinkedListLib = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:Lib"].abi))
var linkedListLib = myLinkedListLib.new({from: eth.accounts[0], data: "0x" + testOutput.contracts["e.sol:Lib"].bin, gas: 4700000},
  function (e, contract) {
    console.log(e, contract);
    if (typeof contract.address !== 'undefined') {
         console.log('Lib mined! address: ' + contract.address.substring(2) + ' transactionHash: ' + contract.transactionHash);

         var arrayCode = testOutput.contracts["e.sol:eBlocBroker"].bin.replace(/__e.sol:Lib__________________+/g, contract.address.substring(2))
         var myArray   = web3.eth.contract(JSON.parse(testOutput.contracts["e.sol:eBlocBroker"].abi));

	     console.log('Submittin eBlocBroker...');
		 arrayCode = "0x" + arrayCode;
         var eBlocBroker = myArray.new({from: eth.accounts[0], data: arrayCode, gas: 6000000},
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

```
cd $HOME/eBlocBroker/eblocbroker/
nano address.json # cp eBlocBroker mined! address =========> eblocbroker/address.json
nano abi.json     # cp printed_ABI                =========> eblocbroker/abi.json
./fixAbi.sh
```
