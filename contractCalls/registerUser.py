#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

if not web3.isConnected():
    print('notconnected')
    sys.exit()

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if len(sys.argv) == 8:
        account = web3.eth.accounts[int(sys.argv[1])];
        userEmail          = str(sys.argv[2]);
        federationCloudID  = str(sys.argv[3]);
        miniLockID         = str(sys.argv[4]);
        ipfsAddress        = str(sys.argv[5]);
        orcid              = str(sys.argv[6]);
        githubUserName     = str(sys.argv[7]);
    else:
        account            = web3.eth.accounts[0]; # User's Ethereum Address
        userEmail          = "alper.alimoglu@gmail.com";
        federationCloudID  = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
        miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
        ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf";
        orcid              = "0000-0001-7642-0552";
        githubUserName     = "eBloc";

    if len(federationCloudID) < 128 and len(userEmail) < 128 and len(orcid) == 19 and orcid.replace("-", "").isdigit(): #{
        tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerUser(userEmail, federationCloudID, miniLockID, ipfsAddress, orcid, githubUserName);
        print('Tx: ' + tx.hex());
#}
