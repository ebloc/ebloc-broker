from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys;

from hexbytes import (
    HexBytes,
)

receiver_pub='0x041574ff388a4b1a7257c3ca38b109588be170cf55a7ade13828ecb119b0f390e5d81b44231a95d15cb45930085f7ba863b9234807ebe54deb258de942440a416b'; # obtained from node_1 and assigned here.

topic = '0x13370000'
payloads = [web3.toHex(text="test message :)"), web3.toHex(text="2nd test message")]

web3.shh.post({
        'powTarget': 2.5,
        'powTime': 2,
        'ttl': 60,
        'payload': payloads[0],
        'pubKey': receiver_pub
})
