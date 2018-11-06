#!/usr/bin/env python

from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys, os, json, asyncio;

from hexbytes import (
    HexBytes,
)

def handle_event(event):
   #print(event)
   print(event['payload'].decode("utf-8"));
   return True
    # and whatever

async def log_loop(event_filter, poll_interval):
	counter=0
	while True:
		# print(counter)
		if counter == 5:
			break
		for event in event_filter.get_new_entries():
			if handle_event(event):
				return
		await asyncio.sleep(poll_interval)
		counter += 1

def main():
   topic = '0x07678231'

   if not os.path.isfile('data.txt'):
   	# First time running:
	   print('Initializing...')
	   kId = web3.shh.newKeyPair()
	   publicKey = web3.shh.getPublicKey(kId)

	   myFilter = web3.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
	   myFilter.poll_interval = 600; #make it equal with the live-time of the message
	   filterID = myFilter.filter_id

	   data = {}
	   data['kId'] = kId
	   data['publicKey'] = publicKey
	   data['filterID'] = filterID

	   with open('data.txt', 'w') as outfile:
		   json.dump(data, outfile)
   else:
      with open('data.txt') as json_file:
         data = json.load(json_file)
         kId = data['kId']
      publicKey = data['publicKey']

   print(publicKey)

   myFilter = web3.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
   myFilter.poll_interval = 600; #make it equal with the live-time of the message
   filterID = myFilter.filter_id

   # Obtained from node_1 and assigned here.
   receiver_pub = "0x04b3b8efbea4fbdcbaee11771a23bb76ec571aee4c0a78e52b0705822146e70a59b8e92eade03393c78b3f6bf6890564abf0ecc664a382cf59c5a59075abc99d6a"

   payloads = [web3.toHex(text=publicKey), web3.toHex(text="2nd test message")]

   web3.shh.post({
        'powTarget': 2, # 2.5
        'powTime': 5,   # 2
        'ttl': 60,
        'payload': payloads[0],
        'topic': topic,
          # 'targetPeer': "",
        'pubKey': receiver_pub,
   })

   loop = asyncio.get_event_loop()
   try:
      loop.run_until_complete(
         asyncio.gather(
            log_loop(myFilter, 2)))
   finally:
      loop.close()

if __name__ == '__main__':
    main()
