# How to do some upgrades

## MAC solc upgrade

```
brew update
brew upgrade
brew tap ethereum/ethereum
brew install solidity
```

## Brownie Upgrade

```
pip install -U eth-brownie
```

-----------------------------------------------------

```
source $HOME/venv/bin/activate
brownie console --network eblocpoa
> web3.eth.blockNumber
```

## Get API

Paste following to get abi into console (`brownie console`):

```
import json
with open('../eblocbroker/abi.json','w') as fp:
    json.dump(eBlocBroker.abi, fp)
```

----------------------------------------------------


```
mv network-config_.yaml ~/.brownie/network-config.yaml
```
