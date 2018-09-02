#!/usr/bin/env python

from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time
print ("web3 =", web3.version.api)

print(web3.shh)
print(web3.shh.version)
print(web3.shh.info)


# keyPair is obtained via web3.shh.newKeyPair();
keyPair =  '0xa82ff6abcf75393084edb06d100e53268c5e118884d59282ef9d3396c8537011'; 

kId = web3.shh.addPrivateKey(keyPair)
print(web3.shh.hasKeyPair(kId))
print('PubKey: ' + web3.shh.getPublicKey(kId))


web3.shh.post({
  'pubKey': web3.shh.getPublicKey(kId),
  'topic': '0x07678231',
  'powTarget': 2.01,
  'powTime': 2,
  'ttl': 10,
  'payload': web3.toHex(text="Hello World!")

});
time.sleep(1)

# Watch --------------
myFilter = web3.shh.newMessageFilter({'topic': '0x07678231', 'privateKeyID': kId});
myFilter.poll_interval = 5; #0.1
print('FilterID: ' + myFilter.filter_id);

retreived_messages = web3.shh.getMessages('9183e6b3c6e20bb7d679579d2b4e305db746e29a4496c60e865d845168509973')

for i in range(0, len(retreived_messages)): #{
    print(retreived_messages[i]['payload'].decode("utf-8"));
    print(retreived_messages[i]);
#}

