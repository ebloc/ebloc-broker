#!/usr/bin/env python3

# To run:
# ./whisperStateReceiver.py 0 # Logs into a file
# ./whisperStateReceiver.py 1 # Prints into console

# from web3.auto import w3
import asyncio
import lib
import json
import sys
import os.path

from os.path import expanduser
from web3 import Web3, HTTPProvider

w3 = Web3(HTTPProvider("http://localhost:8545"))

home = expanduser("~")
my_env = os.environ.copy()

topic = "0x07678231"
testFlag = True
publicKey = None


def log(strIn):
    if testFlag:
        print(strIn)
    else:
        txFile = open(lib.LOG_PATH + "/whisperStateReceiverLog.out", "a")
        txFile.write(strIn + "\n")
        txFile.close()


def post(recipientPublicKey):
    # https://stackoverflow.com/a/50095154/2402577
    status, res = lib.executeShellCommand(["sinfo", "-h", "-o%C"])
    output = res[0].split("/")
    allocatedCore = output[0]
    idleCore = output[1]

    if publicKey != recipientPublicKey:
        try:
            w3.geth.shh.post(
                {
                    "powTarget": 2,  # 2.5
                    "powTime": 5,  # 2
                    "ttl": 60,
                    "payload": w3.toHex(text="online/" + allocatedCore + "/" + idleCore),
                    "topic": topic,
                    "pubKey": recipientPublicKey,
                }
            )
        except:
            post(recipientPublicKey)


def handle_event(event):
    message = event["payload"].decode("utf-8")
    recipientPublicKey = event["recipientPublicKey"].hex()
    log(message)
    post(recipientPublicKey)


async def log_loop(filter_id, poll_interval):
    while True:
        for event in w3.geth.shh.getMessages(filter_id):  # event_filter.get_new_entries():
            handle_event(event)  # TODO: add try catch
        await asyncio.sleep(poll_interval)


def receiver(kId, filter_id, myFilter):
    retreived_messages = w3.geth.shh.getMessages(filter_id)
    log("whisperID (public key)=" + publicKey)

    """
    log('FilterID: ' + filter_id)
    log('receiverPrivateK: ' + w3.geth.shh.getPrivateKey(kId));
    log(w3.geth.shh.hasKeyPair(kId))
	log('PubKey: ' + w3.geth.shh.getPublicKey(kId))
	"""
    # retreived_messages = w3.geth.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')
    log("Received Messages:\n")
    for i in range(0, len(retreived_messages)):
        # log(retreived_messages[i])
        log(retreived_messages[i]["payload"].decode("utf-8"))
        log("---------------------------------")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(filter_id, 2)))
    finally:
        loop.close()


def main(_testFlag=False):
    global testFlag, publicKey
    if _testFlag:
        testFlag = False
    else:
        testFlag = True

    if not os.path.isfile(home + "/.eBlocBroker/whisperInfo.txt"):
        # First time running:
        log("Please first run: python whisperInitialize.py")
        sys.exit()
    else:
        with open(home + "/.eBlocBroker/whisperInfo.txt") as json_file:
            data = json.load(json_file)

        kId = data["kId"]
        publicKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            log("Whisper node's private key of a key pair did not match with the given ID")
            sys.exit()

        # myFilter = w3.geth.shh.newMessageFilter({'topic': topic, 'privateKeyID': kId, 'recipientPublicKey': publicKey})
        # myFilter.poll_interval = 600; # Make it equal with the live-time of the message
        filter_id = data["filter_id"]
        log("filter_id=" + filter_id)
        myFilter = w3.eth.filter(filter_id=filter_id)
        # privateKey = "0xc0995bb51a0a74fcedf972662569849de4b4d0e8ceca8e4e6e8846a5d00f0b0c"
        # kId = w3.geth.shh.addPrivateKey(privateKey)

    receiver(kId, filter_id, myFilter)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main("1")
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Please enter correct number of arguments")
        sys.exit()
