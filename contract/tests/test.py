#!/usr/bin/python3

import os, pytest, sys, base58, binascii

cwd           = os.getcwd()
gasUsed       = []
blockNumber   = []
runTime       = []
blkArrayIndex = 0
myGas         = 0

class cacheType:
    private = 0
    public = 1
    none = 2
    ipfs = 3

class storageID:
    ipfs = 0
    eudat = 1
    ipfs_miniLock = 2
    github = 3
    gdrive = 4
    
Qm = b'\x12 '

def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")

def pushBlockInfo(contract_address):
    global blkArrayIndex
    global gasUsed
    global blockNumber
    global flag

    global myGas
    myGas = contract_address["gasUsed"]
    gasUsed.append(contract_address["gasUsed"])
    blockNumber.append(contract_address["blockNumber"])
    blkArrayIndex = blkArrayIndex + 1

    print("Receipt Used Gas: " + str(contract_address["gasUsed"]))
    return

def receiptCheck(my_contract, chain, web3, e, ipfsHash, index, timeToRun, dataTransferIn, dataTransferOut):
    ipfsBytes32    = convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    set_txn_hash     = my_contract.transact().receiptCheck(ipfsHash,
                                                           index,
                                                           timeToRun,
                                                           resultIpfsHash,
                                                           0,
                                                           e,
                                                           dataTransferIn,
                                                           dataTransferOut)
    contract_address = chain.wait.for_receipt(set_txn_hash)
    pushBlockInfo(contract_address)

def test_receipt(web3, accounts, chain):    
    global blkArrayIndex
    global runTime
	
    web3._requestManager = web3.manager
    my_contract, _       = chain.provider.get_or_deploy_contract('eBlocBroker')
    
    print('Contract\'s Owner: ' + str(my_contract.call().getOwner()))		
    print(accounts)

    account = accounts[0]
    print("\n")

    for i in range(0, 9):
	    print(web3.eth.getBalance(accounts[i]))

    print(account)
    whisperPubKey = "0x04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
    priceCoreMin      = 1
    priceDataTransfer = 1    
    priceStorage      = 1    
    priceCache        = 1    
    web3.eth.defaultAccount = accounts[0]    
    set_txn_hash     = my_contract.transact().registerCluster( "cluster@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, priceCoreMin, priceDataTransfer, priceStorage, priceCache, "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf", whisperPubKey)
    contract_address = chain.wait.for_receipt(set_txn_hash)
    print("usedGas registerCluster: " + str(contract_address["gasUsed"]))
    
    listOfBlockNum = my_contract.call().getClusterPricesBlockNumbers(web3.eth.defaultAccount)
    print("List of blockNumbers")
    print(listOfBlockNum)    

    web3.eth.defaultAccount = accounts[8]
    print('USER ADDRESS: ' + web3.eth.defaultAccount)
    set_txn_hash     = my_contract.transact({"from": accounts[7]}).registerUser("email@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf", 'ebloc', whisperPubKey)
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    print("usedGas registerUser: " + str(contract_address["gasUsed"]))

    set_txn_hash     = my_contract.transact({"from": accounts[8]}).registerUser("email@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf", 'ebloc', whisperPubKey)
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    print("usedGas registerUser: " + str(contract_address["gasUsed"]))

    # ------------
    set_txn_hash = my_contract.transact({"from": accounts[0]}).authenticateOrcID(accounts[8], '0000-0001-7642-0552') # ORCID should be registered.
    print("usedGas authenticateOrcID: " + str(chain.wait.for_receipt(set_txn_hash)["gasUsed"]))    
    assert my_contract.call().isUserOrcIDVerified(accounts[8]), "isUserOrcIDVerified is failed"
    # ------------
    print("isUserExist: "           + str(my_contract.call().isUserExist(accounts[8])))
    blockReadFrom, b = my_contract.call().getUserInfo(accounts[8])
    print("User's blockReadFrom:  " + str(blockReadFrom))

    output = my_contract.call().isUserExist(accounts[1])
    print("isUserExist: " + str(output))

    web3.eth.defaultAccount = accounts[0]
    output = my_contract.call().isClusterExist(accounts[0])
    print("isExist: "+str(output))

    blockReadFrom, coreLimit, priceCoreMin, priceDataTransfer, priceStorage, priceCache = my_contract.call().getClusterInfo(account)
    print("Cluster's coreLimit:  " + str(coreLimit))

    web3.eth.defaultAccount = accounts[0]
    set_txn_hash     = my_contract.transact().updateCluster("cluster@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 128, priceCoreMin, priceDataTransfer, priceCache, priceCache, "0x", whisperPubKey)   

    blockReadFrom, coreLimit, priceCoreMin, priceDataTransfer, priceStorage, priceCache = my_contract.call().getClusterInfo(account)
    print("Cluster's coreLimit:  " + str(coreLimit))

    listOfBlockNum = my_contract.call().getClusterPricesBlockNumbers(web3.eth.defaultAccount)
    print("List of blockNumbers")
    print(listOfBlockNum)    

    web3.eth.defaultAccount = accounts[0]
    set_txn_hash     = my_contract.transact().deregisterCluster()
    contract_address = chain.wait.for_receipt(set_txn_hash)
            
    initial_myGas = contract_address["gasUsed"]
    print("usedGas empty:23499: " + str(initial_myGas))
    #print(initial_myGas)
    #web3.coinbase = accounts[0]
    #web3.coinbase
    web3.eth.defaultAccount = accounts[2]
    set_txn_hash     = my_contract.transact().registerCluster("cluster@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 128, priceCoreMin, priceDataTransfer, priceStorage, priceCache, "0x", whisperPubKey)
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    
    currBlk = web3.eth.blockNumber
    fname = cwd + '/test.txt'    
    f1    = open(cwd + '/receipt.txt', 'w+')
    account = accounts[2]
    blockReadFrom, coreLimit, priceCoreMin, priceDataTransfer, priceStorage, priceCache  = my_contract.call().getClusterInfo(account)
    print("Cluster's coreLimit:  "    + str(coreLimit))
    print("Cluster's priceCoreMin:  " + str(priceCoreMin))

    x = "5b0f93fa7d28bc881f16c14b7c59a58ae5af997e3d0949d7ae6949302bd1f4d0"
    index = 0
    with open(fname) as f: 
        for line in f:
            arguments = line.rstrip('\n').split(" ")

            gasCoreMin     = int(arguments[1]) - int(arguments[0])
            dataTransferIn  = 100
            dataTransferOut = 100
            gasStorageHour  = 1
            core = int(arguments[2])

            chain.wait.for_block(int(arguments[0]))
            jobKey         = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"

            ipfsBytes32 = convertIpfsToBytes32(jobKey)
            sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
            print(sourceCodeHash)
            # sourceCodeHash = "e3fbef873405145274256ee0ee2b580f"
            miniLockId     = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k"
 
			# print("Client Balance before: " + str(web3.eth.getBalance(account)))
			# print("Contract Balance before: " + str(web3.eth.getBalance(accounts[0])))
            # jobPriceValue = 60 * 10000000000000000 * core

            # execution cost + BW-100MB cost is paid
                       
            computationalCost = priceCoreMin * core * gasCoreMin

            jobReceivedBlocNumber, jobGasStorageHour = my_contract.call().getJobStorageTime(account, sourceCodeHash);
            if jobReceivedBlocNumber + jobGasStorageHour * 240 > web3.eth.blockNumber:
                dataTransferIn = 0; # storageCost and cacheCost will be equaled to 0
                
            storageCost = priceStorage * dataTransferIn * gasStorageHour
            cacheCost   = priceCache * dataTransferIn
            
            dataTransferSum  = dataTransferIn + dataTransferOut
            dataTransferCost = priceDataTransfer * dataTransferSum
           
            jobPriceValue = computationalCost + dataTransferCost + storageCost + cacheCost
            
            print('jobPriceValue: ' + str(jobPriceValue))
            set_txn_hash = my_contract.transact({"from": accounts[8],
                                                 "value":web3.toWei(jobPriceValue, "wei"
                                                )}).submitJob(account, jobKey, core, gasCoreMin, dataTransferIn, dataTransferOut, storageID.ipfs, sourceCodeHash, cacheType.private, gasStorageHour)
            contract_address = chain.wait.for_receipt(set_txn_hash)
            print("submitJob: " + str(contract_address["gasUsed"]))
            
			# print("Contract Balance after: " + str(web3.eth.getBalance(accounts[0])))
			# print("Client Balance after: " + str(web3.eth.getBalance(accounts[8])))				
            sys.stdout.write('jobInfo: ')
            sys.stdout.flush()

            print(my_contract.call().getJobInfo('0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d', jobKey, index))
            index += 1
    
    chain.wait.for_block(100)
    print("Block_Number: " + str(web3.eth.blockNumber))

    val = 0
    with open(fname) as f: 
        for line in f: 
            arguments = line.rstrip('\n').split(" ")
            set_txn_hash = my_contract.transact().setJobStatus("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", val, 4, int(arguments[0]))    
            val = val + 1

    print('----------------------------------')
    val = 0
    receivedAmount_temp = 0
    with open(fname) as f: 
        for line in f: 
            arguments = line.rstrip('\n').split(" ")
            dataTransferIn  = 0
            dataTransferOut = 100
            receiptCheck(my_contract, chain, web3, int(arguments[1]), "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd",
                         val, int(arguments[1]) - int(arguments[0]), dataTransferIn, dataTransferOut)
            receivedAmount = my_contract.call().getClusterReceivedAmount(account)            
            print('Cluster Receeived Amount: ' + str(receivedAmount - receivedAmount_temp))
            receivedAmount_temp = receivedAmount
            val += 1
            
    print('----------------------------------')
    print('StorageTime for job: ' + jobKey)
    
    print(my_contract.call().getJobStorageTime(account, sourceCodeHash))
    print('----------------------------------')
    print(my_contract.call({"from": account}).getReceiveStoragePayment(accounts[8], sourceCodeHash))
    
    set_txn_hash = my_contract.transact({"from": account}).receiveStoragePayment(accounts[8], sourceCodeHash);
    contract_address = chain.wait.for_receipt(set_txn_hash)
    print("receiveStoragePayment: " + str(contract_address["gasUsed"]))
    print(my_contract.call({"from": account}).getReceiveStoragePayment(accounts[8], sourceCodeHash))
    print('----------------------------------')
    
    # Prints finalize version of the linked list.
    size = my_contract.call().getClusterReceiptSize(account)
    for i in range(0, size):
        print(my_contract.call().getClusterReceiptNode(account, i))
                 
    print("END")
