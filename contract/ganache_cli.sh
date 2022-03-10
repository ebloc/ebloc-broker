#!/bin/bash
PORT=8547
sed -i 's/\(port: \).*/\1'$PORT'/' ~/.brownie/network-config.yaml
ganache-cli --port $PORT --gasLimit 6721975 --accounts 100 --hardfork istanbul --allowUnlimitedContractSize
