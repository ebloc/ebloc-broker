#!/usr/bin/python3

from brownie import *
import os, time
import scripts.eBlocBroker, scripts.lib, sys

def blockTimestamp(skip=True): return web3.eth.getBlock(web3.eth.blockNumber).timestamp;

def setup():
    scripts.eBlocBroker.main()
    global eB, whisperPubKey, cwd, providerEmail, federatedCloudID, miniLockID, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache, commitmentBlockNum, ipfsAddress, prices, zeroAddress
    
    eB = eBlocBroker[0]
    whisperPubKey = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
    cwd           = os.getcwd()
    
    providerEmail       = "provider@gmail.com"    
    federatedCloudID   = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    availableCoreNum   = 128
    priceCoreMin       = 1
    priceDataTransfer  = 1
    priceStorage       = 1
    priceCache         = 1
    prices             = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]
    commitmentBlockNum = 10
    ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
    zeroAddress        = '0x0000000000000000000000000000000000000000'
       
def getOwner(skip=False):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]
    try:
        eB.transferOwnership(zeroAddress, {"from": accounts[0]})
    except:
        print('revert detected.')
        
    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]
    
def updateProvider(skip=False, printFlag=True):
    rpc.mine(5)
    registerProvider(False, True)
    # print(tx.events['LogProviderInfo'])
        
    federatedCloudID  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateProviderInfo(providerEmail,
                              federatedCloudID,
                              miniLockID,
                              ipfsAddress,
                              whisperPubKey, {'from': accounts[0]})
    if printFlag:
        print('updateProviderInfo => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    # rpc.mine(int(arguments[0]))
    availableCoreNum  = 64
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateProviderPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    availableCoreNum  = 16
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateProviderPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    rpc.mine(16)
    availableCoreNum  = 32
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    if printFlag:
        print('updateProviderPrices => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       

    providerPriceInfo   = eB.getProviderInfo(accounts[0])
    blockReadFrom      = providerPriceInfo[0]
    print(blockReadFrom)
    # assert blockReadFrom == 20
    print(eB.getProviderSetBlockNumbers(accounts[0]))
    
    # eB.pauseProvider({'from': accounts[4]})
    
def registerProvider(skip=True, printFlag=True):
    '''Register Provider'''
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]

    tx = eB.registerProvider(providerEmail, federatedCloudID, miniLockID, availableCoreNum, priceCoreMin, priceDataTransfer,
                            priceStorage, priceCache, commitmentBlockNum, ipfsAddress, whisperPubKey, {'from': accounts[0]})
    if printFlag:
        print('\nregisterProvider => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))       


def registerRequester(skip=True, printFlag=True):
    '''Register Requester'''
    tx     = eB.registerRequester("email@gmail.com",
                             "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
                             "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ",
                             "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
                             'ebloc',
                             whisperPubKey, {'from': accounts[1]})
    if printFlag:
        print('registerRequester => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))

    assert eB.isRequesterExists(accounts[1]), True
    blockReadFrom, b = eB.getRequesterInfo(accounts[1])

    tx = eB.authenticateOrcID(accounts[1], '0000-0001-7642-0552', {'from': accounts[0]}) # ORCID should be registered.
    print('authenticateOrcID => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))    
    assert eB.isRequesterOrcIDVerified(accounts[1]), "isRequesterOrcIDVerified is failed"

def multipleData(skip=False):
    registerProvider(False)
    registerRequester(False)                    
    _provider = accounts[0]
    _requester = accounts[1]    

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

    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, _provider, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)

    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # ---
    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, _provider, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)
        
    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))          
    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # Provider Side:
    index = 0
    jobID = 0
    startTime = blockTimestamp()
    jobExecutionTimeMin = 10
    resultIpfsHash = '0xabcd'
    tx = eB.setJobStatus(jobKey, index, jobID, 2, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * jobExecutionTimeMin)
    rpc.mine(1)
    endTime = startTime + 15 * 4 * jobExecutionTimeMin

    tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum = tx.events['LogReceipt']['receivedWei']
    refundedSum = tx.events['LogReceipt']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
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

    tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum = tx.events['LogReceipt']['receivedWei']
    refundedSum = tx.events['LogReceipt']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))

def workFlow(skip=False):
    registerProvider(False)
    registerRequester(False)                    
    _provider = accounts[0]
    _requester    = accounts[1]    

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

    jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, _provider, eB, sourceCodeHashArray, web3,
                                     dataTransferInArray, dataTransferOut, cacheHourArray)
                
    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                      storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
    print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))          
    print(eB.getJobInfo(_provider, jobKey, 0, 0))
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
    refundedSum = 0
    # receiptCheck for the workflow: -------------
    index = 0
    jobID = 0
    jobExecutionTimeMin = 10
    dataTransfer = [100, 0]
    endTime = 20
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']
    # --------
    index = 0
    jobID = 1
    jobExecutionTimeMin = 15
    dataTransfer = [0, 0]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('\nreceiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']

    # --------

    index = 0
    jobID = 2
    jobExecutionTimeMin = 20
    dataTransfer = [0, 100]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray,
                         {"from": accounts[0]})
    print('\nreceiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']

    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))
    
    assert(jobPriceValue == receivedSum + refundedSum)

    eB.updateDataReceivedBlock(resultIpfsHash, {"from": accounts[4]})
    
def submitJob(skip=False):
    # def submitJob(skip=True):    
    registerProvider(False)
    registerRequester(False)                    
    _provider = accounts[0]
    _requester = accounts[1]    
    
    print(cwd)
    fname = cwd + '/files/test.txt'
    # fname = cwd + '/files/test_.txt'

    print('Registered provider addresses:')
    print(eB.getProviders())
    
    providerPriceInfo   = eB.getProviderInfo(accounts[0])    
    blockReadFrom      = providerPriceInfo[0]
    availableCoreNum   = providerPriceInfo[1]    
    priceCoreMin       = providerPriceInfo[2]
    priceDataTransfer  = providerPriceInfo[3]
    priceStorage       = providerPriceInfo[4]
    priceCache         = providerPriceInfo[5]
    commitmentBlockNum = providerPriceInfo[6]
    
    print("Provider's availableCoreNum:  " + str(availableCoreNum))
    print("Provider's priceCoreMin:  "     + str(priceCoreMin))
    print(providerPriceInfo)

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
            jobPriceValue = scripts.lib.cost(coreArray, coreMinArray, _provider, eB, sourceCodeHashArray, web3,
                                             dataTransferInArray, dataTransferOut, cacheHourArray)
            jobPriceValueSum   += jobPriceValue
            storageID_cacheType = [scripts.lib.storageID.ipfs, scripts.lib.cacheType.private]
            dataTransferInArray = [dataTransferIn]
            
            tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                              storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                              {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
            print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
            print('jobIndex=' + str(tx.events['LogJob']['index']))
                        
			# print("Contract Balance after: " + str(web3.eth.getBalance(accounts[0])))
			# print("Client Balance after: " + str(web3.eth.getBalance(accounts[8])))				
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(eB.getJobInfo(_provider, jobKey, index, jobID))
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
                dataTransferIn  = 90
                dataTransferOut = 100
            else:
                dataTransferIn  = 0
                dataTransferOut = 100

            print('\nContractBalance=' + str(eB.getContractBalance()))                
            dataTransfer = [dataTransferIn, dataTransferOut]
            jobID = 0
            jobExecutionTimeMin = int(arguments[1]) - int(arguments[0])            
            tx = eB.receiptCheck(jobKey, [index, jobID], jobExecutionTimeMin, resultIpfsHash, int(arguments[1]), dataTransfer, sourceCodeHashArray,
                                 {"from": accounts[0]})
            print('receiptCheck => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))

            received = tx.events['LogReceipt']['receivedWei']
            refunded = tx.events['LogReceipt']['refundedWei']
            print('received=' + str(received) + '| refunded=' + str(refunded))           
            index += 1

    print('\nContractBalance=' + str(eB.getContractBalance()))                
    # Prints finalize version of the linked list.
    size = eB.getProviderReceiptSize(_provider)
    for i in range(0, size):
        print(eB.getProviderReceiptNode(_provider, i))

    print('----------------------------------')
    print('StorageTime for job: ' + jobKey)
    ret = eB.getJobStorageTime(_provider, sourceCodeHash)
    print('ReceivedBlockNumber=' + str(ret[0]) + ' | ' + 'cacheDuration=' + str(ret[1] * 240))
    print('----------------------------------')          
    print(eB.getReceiveStoragePayment(_requester, sourceCodeHash, {"from": _provider}))
    
    '''
    rpc.mine(240)
    tx = eB.receiveStoragePayment(_requester, sourceCodeHash, {"from": _provider});
    print('receiveStoragePayment => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceiveStoragePayment(_requester, sourceCodeHash, {"from": _provider}))
    print('----------------------------------') 
    '''
    
