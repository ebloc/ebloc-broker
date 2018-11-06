#!/usr/bin/env python

from web3.auto import w3
import asyncio
from web3 import Web3, HTTPProvider
from web3.shh import Shh

import json,sys,os.path

def handle_event(event):
   #print(event)
   print(event['payload'].decode("utf-8"));
    # and whatever

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)
	
def main():
	topic = '0x07678231'
	
	web3 = Web3(HTTPProvider('http://localhost:8545'))
	Shh.attach(web3, "shh")
	print(web3.shh.info)
			
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
		myFilter = web3.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
		myFilter.poll_interval = 600; #make it equal with the live-time of the message
		filterID = data['filterID']
		# privateKey = "0xc0995bb51a0a74fcedf972662569849de4b4d0e8ceca8e4e6e8846a5d00f0b0c" 
		# kId = web3.shh.addPrivateKey(privateKey)

	retreived_messages = web3.shh.getMessages(filterID)

	print('publicKeyK: ' + publicKey);
	'''
	print('FilterID: ' + filterID)	
	print('receiverPrivateK: ' + web3.shh.getPrivateKey(kId));		
	print(web3.shh.hasKeyPair(kId))
	print('PubKey: ' + web3.shh.getPublicKey(kId))
	'''
	# retreived_messages = web3.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')	
				
	for i in range(0, len(retreived_messages)):
		print(retreived_messages[i]['payload'].decode("utf-8"))
		print('---------------------------------')
		# print(retreived_messages[i])

	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(
			asyncio.gather(
				log_loop(myFilter, 2)))
	finally:
		loop.close()

if __name__ == '__main__':
    main()
