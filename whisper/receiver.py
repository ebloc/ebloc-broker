#!/usr/bin/env python

from web3.auto import w3
import asyncio
from web3 import Web3, HTTPProvider
from web3.shh import Shh

def handle_event(event):
    print(event)
    print(event['payload'].decode("utf-8"));
    # and whatever

async def log_loop(event_filter, poll_interval): #{
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)
#}

def main(): #{
    web3 = Web3(HTTPProvider('http://localhost:8545'))
    Shh.attach(web3, "shh")
    print(web3.shh.info)

    '''
    # First time running:
    kId = web3.shh.newKeyPair()
    receiver_pub = web3.shh.getPublicKey(kId)
    print('receiverPubK: '     + receiver_pub);
    print('receiverPrivateK: ' + web3.shh.getPrivateKey(kId));
    '''
    
    privateKey = '0x5fc212a0774add56f4a32b59a1cf6100ae0ef8fe1481c1ab7d011796d1e53320' 
    kId = web3.shh.addPrivateKey(privateKey)

    print(web3.shh.hasKeyPair(kId))
    print('PubKey: ' + web3.shh.getPublicKey(kId))
    myFilter = web3.shh.newMessageFilter({'topic': '0x07678231', 'privateKeyID': kId})
    myFilter.poll_interval = 600; #make it equal with the live-time of the message
    print('FilterID: ' + myFilter.filter_id)

    retreived_messages = web3.shh.getMessages('c173ea8111b199b3b88255ac0e6c395b7a1dfe1e771457dad66bac8b87cb19ca') 
    for i in range(0, len(retreived_messages)):
        print(retreived_messages[i]['payload'].decode("utf-8"))
        print(retreived_messages[i])

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(myFilter, 2)))
    finally:
        loop.close()
#}

if __name__ == '__main__': #{
    main()
#}

# existing_filter = web3.eth.filter(filter_id='6254aaa148f4077340e66cf1ea488529308146348f74ea382f44c8af05f1b023')
