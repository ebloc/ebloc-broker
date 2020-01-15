# Upgrades

## MAC solc upgrade

brew update
brew upgrade
brew tap ethereum/ethereum
brew install solidity

## Brownie Upgrade

pip install eth-brownie -U


source $HOME/v/bin/activate
brownie console --network private
> web3.eth.blockNumber

Paste following to get abi into console:

```
import json
with open('abi.json','w') as fp:
    json.dump(eBlocBroker.abi, fp)
```
# // , indent=2
