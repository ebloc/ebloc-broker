#!/usr/bin/python3

from brownie import *
import os, time
import scripts.token, scripts.lib, sys
    
def blockTimestamp(skip=True): return web3.eth.getBlock(web3.eth.blockNumber).timestamp;

def setup():
    scripts.token.main()
    global eB, whisperPubKey, cwd, clusterEmail, federatedCloudID, miniLockID, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache, commitmentBlockNum, ipfsAddress, prices
    
    eB = eBlocBroker[0]
    whisperPubKey = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
    cwd           = os.getcwd()
    
    clusterEmail       = "cluster@gmail.com"    
    federatedCloudID   = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    availableCoreNum   = 128
    priceCoreMin       = 1
    priceDataTransfer  = 1
    priceStorage       = 1
    priceCache         = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]
    commitmentBlockNum = 10
    ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
       
def getOwner(skip=False):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]
    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]
    
def updateCluster(skip=False, printFlag=True):
    rpc.mine(5)
    registerCluster(False, True)
    # print(tx.events['LogClusterInfo'])
        
    federatedCloudID  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateClusterInfo(clusterEmail,
                              federatedCloudID,
                              miniLockID,
                              ipfsAddress,
                              whisperPubKey, {'from': accounts[0]})
    if printFlag:
        print('updateClusterInfo => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    # rpc.mine(int(arguments[0]))
    availableCoreNum  = 64
    tx = eB.updateClusterPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateClusterPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    availableCoreNum  = 16
    tx = eB.updateClusterPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateClusterPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    rpc.mine(16)
    availableCoreNum  = 32
    tx = eB.updateClusterPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateClusterPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    clusterPriceInfo   = eB.getClusterInfo(accounts[0])
    blockReadFrom      = clusterPriceInfo[0]
    print(blockReadFrom)
    # assert blockReadFrom == 20
    print(eB.getClusterSetBlockNumbers(accounts[0]))
    
    # eB.pauseCluster({'from': accounts[4]})
    
def registerCluster(skip=True, printFlag=True):
    '''Register Cluster'''
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]

    tx = eB.registerCluster(clusterEmail, federatedCloudID, miniLockID, availableCoreNum, priceCoreMin, priceDataTransfer,
                            priceStorage, priceCache, commitmentBlockNum, ipfsAddress, whisperPubKey, {'from': accounts[0]})
    if printFlag:
        print('\nregisterCluster => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       


def registerUser(skip=True, printFlag=True):
    '''Register User'''
    tx     = eB.registerUser("email@gmail.com",
                             "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
                             "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ",
                             "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
                             'ebloc',
                             whisperPubKey, {'from': accounts[1]})
    if printFlag:
        print('registerUser => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))

    assert eB.isUserExists(accounts[1]), True
    blockReadFrom, b = eB.getUserInfo(accounts[1])

    tx = eB.authenticateOrcID(accounts[1], '0000-0001-7642-0552', {'from': accounts[0]}) # ORCID should be registered.
    print('authenticateOrcID => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))    
    assert eB.isUserOrcIDVerified(accounts[1]), "isUserOrcIDVerified is failed"

def multipleData(skip=False):
    registerCluster(False)
    registerUser(False)                    
    clusterAddress = accounts[0]
    userAddress    = accounts[1]    

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash_1 = web3.toBytes(hexstr= ipfsBytes32)
    cacheHour_1      = 1

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey_2)
    sourceCodeHash_2 = web3.toBytes(hexstr= ipfsBytes32)
    cacheHour_2      = 1
    
    sourceCodeHashArray = [sourceCodeHash_1, sourceCodeHash_2] # Hashed of the
    cacheHourArray      = [cacheHour_1, cacheHour_2]
            
    dataTransferIn_1  = 100
    dataTransferIn_2  = 100
    dataTransferOut = 100
    dataTransferInArray  = [dataTransferIn_1, dataTransferIn_2]    
    dataTransfer         = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    coreArray       = [2]    
    coreMinArray    = [10]
    
    storageID_cacheType = [scripts.lib.storageID.ipfs, scripts.lib.cacheType.private]

    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, clusterAddress, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)
    
    tx = eB.submitJob(clusterAddress, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": userAddress, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # ---
    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, clusterAddress, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)
        
    tx = eB.submitJob(clusterAddress, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": userAddress, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))          
    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # Cluster Side:
    index = 0
    jobID = 0
    startTime = blockTimestamp()
    jobExecutionTimeMin = 10
    resultIpfsHash = '0xabcd'
    tx = eB.setJobStatus(jobKey, index, jobID, 2, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * jobExecutionTimeMin)
    rpc.mine(1)
    endTime = startTime + 15 * 4 * jobExecutionTimeMin

    tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum = tx.events['LogReceipt']['received']
    returnedSum = tx.events['LogReceipt']['returned']
    print(str(receivedSum) + ' ' + str(returnedSum))
    # --
    dataTransferIn  = 0 # already requested on index==0
    dataTransferOut = 100
    dataTransfer    = [dataTransferIn, dataTransferOut]

    index = 1
    jobID = 0
    startTime = blockTimestamp()
    jobExecutionTimeMin = 10
    resultIpfsHash = '0xabcd'
    tx = eB.setJobStatus(jobKey, index, jobID, 2, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * jobExecutionTimeMin)
    rpc.mine(1)
    endTime = startTime + 15 * 4 * jobExecutionTimeMin

    tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum = tx.events['LogReceipt']['received']
    returnedSum = tx.events['LogReceipt']['returned']
    print(str(receivedSum) + ' ' + str(returnedSum))

def workFlow(skip=False):
    registerCluster(False)
    registerUser(False)                    
    clusterAddress = accounts[0]
    userAddress    = accounts[1]    

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
    cacheHour      = 0
        
    sourceCodeHashArray = [sourceCodeHash] # Hashed of the data file in array
    cacheHourArray      = [cacheHour]

            
    dataTransferIn  = 100
    dataTransferOut = 100
    dataTransferInArray  = [dataTransferIn]
    
    dataTransfer    = [dataTransferIn, dataTransferOut]

    coreArray       = [2,   4,  2]    
    coreMinArray    = [10, 15, 20]
    
    storageID_cacheType = [scripts.lib.storageID.ipfs, scripts.lib.cacheType.private]

    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, clusterAddress, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)
                
    tx = eB.submitJob(clusterAddress, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": userAddress, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))          
    print(eB.getJobInfo(clusterAddress, jobKey, 0, 0))
    print('-----------')
    
    # setJobStatus for the workflow: -------------
    index = 0
    jobID = 0
    startTime = 10
    tx = eB.setJobStatus(jobKey, index, jobID, 2, startTime, {"from": accounts[0]})

    index = 0
    jobID = 1
    startTime = 20
    tx = eB.setJobStatus(jobKey, index, jobID, 2, startTime, {"from": accounts[0]})


    receivedSum = 0
    returnedSum = 0
    # receiptCheck for the workflow: -------------
    index = 0
    jobID = 0
    jobExecutionTimeMin = 10
    dataTransfer = [100, 0]
    endTime = 20
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['received']
    returnedSum += tx.events['LogReceipt']['returned']
    # --------
    index = 0
    jobID = 1
    jobExecutionTimeMin = 15
    dataTransfer = [0, 0]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('\nreceiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['received']
    returnedSum += tx.events['LogReceipt']['returned']

    # --------

    index = 0
    jobID = 2
    jobExecutionTimeMin = 20
    dataTransfer = [0, 100]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('\nreceiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['received']
    returnedSum += tx.events['LogReceipt']['returned']

    print('receivedSum=' + str(receivedSum) + ' | ' + 'returnedSum=' + str(returnedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))
    
    assert(jobPriceValue == receivedSum + returnedSum)

    eB.updateDataReceivedBlock(resultIpfsHash, {"from": accounts[4]})
    
def submitJob(skip=False):
    # def submitJob(skip=True):    
    registerCluster(False)
    registerUser(False)                    
    clusterAddress = accounts[0]
    userAddress = accounts[1]    
    
    print(cwd)
    fname = cwd + '/files/test.txt'
    # fname = cwd + '/files/test_.txt'

    print('Registered cluster addresses:')
    print(eB.getClusterAddresses())
    
    clusterPriceInfo   = eB.getClusterInfo(accounts[0])    
    blockReadFrom      = clusterPriceInfo[0]
    availableCoreNum   = clusterPriceInfo[1]    
    priceCoreMin       = clusterPriceInfo[2]
    priceDataTransfer  = clusterPriceInfo[3]
    priceStorage       = clusterPriceInfo[4]
    priceCache         = clusterPriceInfo[5]
    commitmentBlockNum = clusterPriceInfo[6]
    
    print("Cluster's availableCoreNum:  " + str(availableCoreNum))
    print("Cluster's priceCoreMin:  "     + str(priceCoreMin))
    print(clusterPriceInfo)

    jobPriceValueSum = 0
    jobID = 0    
    index = 0
    with open(fname) as f: 
        for line in f:
            arguments = line.rstrip('\n').split(" ")

            coreMin      = int(arguments[1]) - int(arguments[0])
            cacheHour    = 1
            core         = int(arguments[2])

            # time.sleep(1)
            # rpc.mine(int(arguments[0]))
            
            jobKey         = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd" # Source Code's jobKey
            ipfsBytes32    = scripts.lib.convertIpfsToBytes32(jobKey)
            sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
            
			# print("Client Balance before: " + str(web3.eth.getBalance(account)))
			# print("Contract Balance before: " + str(web3.eth.getBalance(accounts[0])))

            coreArray    = [core]            
            coreMinArray = [coreMin]
            
            sourceCodeHashArray = [sourceCodeHash] # Hashed of the 
            cacheHourArray      = [cacheHour]
            
            dataTransferIn  = 100
            dataTransferOut = 100            

            dataTransferInArray = [dataTransferIn]
            
            print(sourceCodeHashArray[0])
            jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, clusterAddress, eB, sourceCodeHashArray, web3,
                                             dataTransferInArray, dataTransferOut, cacheHourArray)
            jobPriceValueSum   += jobPriceValue
            storageID_cacheType = [scripts.lib.storageID.ipfs, scripts.lib.cacheType.private]
            dataTransferInArray = [dataTransferIn]
            
            tx = eB.submitJob(clusterAddress, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                              storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                              {"from": userAddress, "value": web3.toWei(jobPriceValue, "wei")})
            print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
            print('jobIndex=' + str(tx.events['LogJob']['index']))
                        
			# print("Contract Balance after: " + str(web3.eth.getBalance(accounts[0])))
			# print("Client Balance after: " + str(web3.eth.getBalance(accounts[8])))				
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(eB.getJobInfo(clusterAddress, jobKey, index, jobID))
            index += 1

    print('TotalPaid=' + str(jobPriceValueSum))
    # print(blockReadFrom)
    # rpc.mine(100)
    # print(web3.eth.blockNumber)

    jobID = 0
    index = 0
    with open(fname) as f: 
        for line in f: 
            arguments = line.rstrip('\n').split(" ")
            tx = eB.setJobStatus(jobKey, index, jobID, 2, int(arguments[0]),
                                 {"from": accounts[0]})
            index += 1

    print('----------------------------------')
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)
    
    index = 0
    receivedAmount_temp = 0
    with open(fname) as f: 
        for line in f: 
            arguments = line.rstrip('\n').split(" ")
            if index == 0:
                dataTransferIn  = 100
                dataTransferOut = 100
            else:
                dataTransferIn  = 0
                dataTransferOut = 100

            print('\nContractBalance=' + str(eB.getContractBalance()))                
            dataTransfer = [dataTransferIn, dataTransferOut]
            jobID = 0
            jobExecutionTimeMin = int(arguments[1]) - int(arguments[0])            
            tx = eB.receiptCheck(jobKey, index, jobID, jobExecutionTimeMin, resultIpfsHash, int(arguments[1]), dataTransfer, sourceCodeHashArray,
                                 {"from": accounts[0]})
            print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))

            received = tx.events['LogReceipt']['received']
            returned = tx.events['LogReceipt']['returned']
            print('received=' + str(received) + '| returned=' + str(returned))           
            index += 1

    print('\nContractBalance=' + str(eB.getContractBalance()))                
    # Prints finalize version of the linked list.
    size = eB.getClusterReceiptSize(clusterAddress)
    for i in range(0, size):
        print(eB.getClusterReceiptNode(clusterAddress, i))

    print('----------------------------------')
    print('StorageTime for job: ' + jobKey)
    ret = eB.getJobStorageTime(clusterAddress, sourceCodeHash)
    print('ReceivedBlockNumber=' + str(ret[0]) + ' | ' + 'cacheDuration=' + str(ret[1] * 240))
    print('----------------------------------')          
    print(eB.getReceiveStoragePayment(userAddress, sourceCodeHash, {"from": clusterAddress}))
    
    '''
    rpc.mine(240)
    tx = eB.receiveStoragePayment(userAddress, sourceCodeHash, {"from": clusterAddress});
    print('receiveStoragePayment => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceiveStoragePayment(userAddress, sourceCodeHash, {"from": clusterAddress}))
    print('----------------------------------') 
    '''
    
