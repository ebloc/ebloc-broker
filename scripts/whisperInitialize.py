#!/usr/bin/env python3

from web3.auto import w3
import asyncio
from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import json,sys,os.path

from os.path import expanduser
home = expanduser("~")

topic = '0x07678231'

print('Initializing...')
kId = web3.shh.newKeyPair() #Generates a new public and private key pair for message decryption and encryption.
publicKey = web3.shh.getPublicKey(kId)
myFilter = web3.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
myFilter.poll_interval = 600; #make it equal with the live-time of the message
filterID = myFilter.filter_id

data = {}
data['kId'] = kId
data['publicKey'] = publicKey
data['filterID'] = filterID

with open(home + '/.eBlocBroker/whisperInfo.txt', 'w') as outfile:  
	json.dump(data, outfile)

print('Done.')
print('You can access whisper info on ~/.eBlocBroker/whisperInfo.txt')
