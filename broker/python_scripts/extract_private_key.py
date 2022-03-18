#!/usr/bin/env python3

from os.path import expanduser

from web3 import Web3
from web3.providers.rpc import HTTPProvider

_path = expanduser("~/.eblocpoa/keystore/UTC--2020-03-18T13-02-58.306094822Z--d118b6ef83ccf11b34331f1e7285542ddf70bc49")
w3 = Web3(HTTPProvider("127.0.0.1:8545"))
# w3 = Web3(Web3.HTTPProvider("https://core.bloxberg.org"))

with open(_path) as keyfile:
    encrypted_key = keyfile.read()
    private_key = w3.eth.account.decrypt(encrypted_key, "alper")

print(private_key.hex())


# Enter the password to unlock this account:
# SUCCESS: Keystore '~/.eblocpoa/keystore/UTC--2020-03-18T13-02-58.306094822Z--d118b6ef83ccf11b34331f1e7285542ddf70bc49' has been imported with the id 'alper'
