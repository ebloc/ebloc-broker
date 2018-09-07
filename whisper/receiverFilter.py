from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys;

from hexbytes import (
    HexBytes,
)

kId = web3.shh.newKeyPair()
receiver_pub = web3.shh.getPublicKey(kId)

privateKey = '0x5fc212a0774add56f4a32b59a1cf6100ae0ef8fe1481c1ab7d011796d1e53320'
kId = web3.shh.addPrivateKey(privateKey)

print('receiverPubK: ' + receiver_pub);
print('receiverPrivateK: ' + web3.shh.getPrivateKey(kId));

topic = '0x13370000'

shh_filter = web3.shh.newMessageFilter({
    'privateKeyID': kId,
    'topics': [topic]
})

input("Press Enter to continue...");

received_messages = [];
received_messages = shh_filter.get_new_entries()
print(len(received_messages)) # Returns '0'

print(received_messages[0])
print(web3.shh.info.memory)  # Returns '0'
