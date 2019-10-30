#!/usr/bin/python3

import pytest, os, time
import scripts.lib
from brownie import accounts

rows, columns = os.popen('stty size', 'r').read().split()
spaces = ''.join(['-'] * (int(columns)-1))

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

def test_storageRefund(eB, rpc, web3):
    newTest()
    _provider  = accounts[0]
    _requester = accounts[1]    

    registerProvider(eB, rpc, web3)
    registerRequester(eB, rpc, web3, _requester)                        
    
    cacheHourArray = []
    sourceCodeHashArray = []
    
    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHashArray.append(web3.toBytes(hexstr= ipfsBytes32))
    cacheHourArray.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey_2)
    sourceCodeHashArray.append(web3.toBytes(hexstr= ipfsBytes32))
    cacheHourArray.append(1)
        
    dataTransferIn_1  = 100
    dataTransferIn_2  = 100
    dataTransferOut   = 100
    dataTransferInArray  = [dataTransferIn_1, dataTransferIn_2]    
    dataTransfer         = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    coreArray       = [2]    
    coreMinArray    = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.storageID.IPFS, scripts.lib.storageID.IPFS]
    storageID_cacheType = [storageID_list, scripts.lib.cacheType.PRIVATE, providerPriceBlockNumber]
    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, _provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, eB, web3)

    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])

    index = 0
    jobID = 0
    tx = eB.refund(_provider, jobKey, index, jobID, {"from": _provider})
    print(eB.getJobInfo(_provider, jobKey, index, jobID))
    refundedWei = tx.events['LogRefundRequest']['refundedWei']
    print('refundedWei=' + str(refundedWei))
    
    assert (cost['computationalCost'] + cost['dataTransferCost'] + cost['cacheCost'] == refundedWei)

    print(sourceCodeHashArray[0])
    print('=' + str(eB.getReceiveStoragePayment(_provider, _requester, sourceCodeHashArray[0])))
    print('')
    print(sourceCodeHashArray[1])
    print('=' + str(eB.getReceiveStoragePayment(_provider, _requester, sourceCodeHashArray[0])))
     
    rpc.mine(240)
    
    tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events['LogStoragePayment']['payment']
    print('refundedWei=' + str(refundedWei))

    with pytest.reverts(): # refundStoragePayment should revert
        tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})

    tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[1], {"from": _requester, "gas": 4500000})
    refundedWei += tx.events['LogStoragePayment']['payment']
    paidAddress = tx.events['LogStoragePayment']['paidAddress']
        
    with pytest.reverts(): # refundStoragePayment should revert
        tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})

    assert(cost['storageCost'] == refundedWei)
    assert(_requester == paidAddress)
    assert(eB.getProviderReceivedAmount(_provider) == 0)

    # ---------------------------------------------------------------
    print('----Same Job submitted after full refund -----')

    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])

    index = 1
    jobID = 0
    tx = eB.refund(_provider, jobKey, index, jobID, {"from": _provider})
    print(eB.getJobInfo(_provider, jobKey, index, jobID))
    refundedWei = tx.events['LogRefundRequest']['refundedWei']
    print('refundedWei=' + str(refundedWei))
    
    assert (cost['computationalCost'] + cost['dataTransferCost'] + cost['cacheCost'] == refundedWei)

    print(sourceCodeHashArray[0])
    print('=' + str(eB.getReceiveStoragePayment(_provider, _requester, sourceCodeHashArray[0])))
    print('')
    print(sourceCodeHashArray[1])
    print('=' + str(eB.getReceiveStoragePayment(_provider, _requester, sourceCodeHashArray[0])))
       
    print(eB.getJobStorageTime(_provider, _requester, sourceCodeHashArray[0]))
    # Called by the cluster
    eB.sourceCodeHashReceived(jobKey, index, sourceCodeHashArray, {"from": _provider, "gas": 4500000})
       
    print(eB.getJobStorageTime(_provider, _requester, sourceCodeHashArray[0]))      
    print(eB.getJobStorageTime(_provider, _requester, sourceCodeHashArray[1]))   

    with pytest.reverts(): # refundStoragePayment should revert, because it is already used by the provider
        tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})
        tx = eB.refundStoragePayment(_provider, _requester, sourceCodeHashArray[1], {"from": _requester, "gas": 4500000})
        
    with pytest.reverts():
        tx = eB.receiveStoragePayment(_requester, sourceCodeHashArray[0], {"from": _provider})
    
    rpc.mine(240)
    # After deadline (1 hr) is completed to store the data, provider could obtain the money
    tx = eB.receiveStoragePayment(_requester, sourceCodeHashArray[0], {"from": _provider})
    tx = eB.receiveStoragePayment(_requester, sourceCodeHashArray[1], {"from": _provider})

def getBlockTimestamp(web3):
    return web3.eth.getBlock(web3.eth.blockNumber).timestamp;

def newTest():
    print(spaces, end ="")

@pytest.mark.skip(reason="skip")    
def test_ownership(eB):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]
    
    with pytest.reverts(): # transferOwnership should revert
        eB.transferOwnership('0x0000000000000000000000000000000000000000', {"from": accounts[0]})

    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]   

def registerProvider(eB, rpc, web3):
    '''Register Provider'''
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    tx = eB.registerProvider(providerEmail, federatedCloudID, miniLockID, availableCoreNum, prices, commitmentBlockNum, ipfsAddress, whisperPubKey, {'from': accounts[0]})
    
def test_updateProvider(eB, rpc, web3):
    newTest()
    rpc.mine(5)
    registerProvider(eB, rpc, web3)

    federatedCloudID  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateProviderInfo(providerEmail, federatedCloudID, miniLockID, ipfsAddress, whisperPubKey, {'from': accounts[0]})

    availableCoreNum  = 64
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})
    availableCoreNum  = 16
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})

    rpc.mine(16)
    availableCoreNum  = 32
    tx = eB.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, {'from': accounts[0]})

    providerPriceInfo   = eB.getProviderInfo(accounts[0])
    blockReadFrom      = providerPriceInfo[0]
    print(blockReadFrom)
    # assert blockReadFrom == 20
    print(eB.getProviderSetBlockNumbers(accounts[0]))
    
def registerRequester(eB, rpc, web3, _account):
    '''Register Requester'''
    tx = eB.registerRequester("email@gmail.com",
                              "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
                              "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ",
                              "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
                              'ebloc',
                              whisperPubKey, {'from': _account})
    assert eB.isRequesterExists(_account), True
    blockReadFrom, b = eB.getRequesterInfo(_account)

    tx = eB.authenticateOrcID(_account, '0000-0001-7642-0552', {'from': accounts[0]}) # ORCID should be registered.
    assert eB.isRequesterOrcIDVerified(_account), "isRequesterOrcIDVerified is failed"

def test_multipleData(eB, rpc, web3):
    newTest()
    _provider  = accounts[0]
    _requester = accounts[1]    

    registerProvider(eB, rpc, web3)
    registerRequester(eB, rpc, web3, _requester)                        
    
    cacheHourArray = []
    sourceCodeHashArray = []
    
    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHashArray.append(web3.toBytes(hexstr= ipfsBytes32))
    cacheHourArray.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey_2)
    sourceCodeHashArray.append(web3.toBytes(hexstr= ipfsBytes32))
    cacheHourArray.append(1)
        
    dataTransferIn_1  = 100
    dataTransferIn_2  = 100
    dataTransferOut   = 100
    dataTransferInArray  = [dataTransferIn_1, dataTransferIn_2]    
    dataTransfer         = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    coreArray       = [2]    
    coreMinArray    = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.storageID.IPFS, scripts.lib.storageID.IPFS]
    storageID_cacheType = [storageID_list, scripts.lib.cacheType.PRIVATE, providerPriceBlockNumber]
    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, _provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, eB, web3)

    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])    
    
    # ---
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, _provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, eB, web3)

    assert cost['storageCost'] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost['dataTransferCost'] == dataTransferOut, "dataTransferCost should cover only dataTransferOut"
    
    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # Provider Side:--------------------
    index = 0
    jobID = 0
    startTime = getBlockTimestamp(web3)
    executionTimeMin = 10
    resultIpfsHash = '0xabcd'
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * executionTimeMin)
    rpc.mine(1)
    endTime = startTime + 15 * 4 * executionTimeMin

    tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, {"from": accounts[0]})

    receivedSum = tx.events['LogReceipt']['receivedWei']
    refundedSum = tx.events['LogReceipt']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 320 and refundedSum == 0
    
    # --
    dataTransferIn  = 0 # already requested on index==0
    dataTransferOut = 100
    dataTransfer    = [dataTransferIn, dataTransferOut]

    index = 1
    jobID = 0
    startTime = getBlockTimestamp(web3)
    executionTimeMin = 10
    resultIpfsHash = '0xabcd'
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * executionTimeMin)
    rpc.mine(1)
    endTime = startTime + 15 * 4 * executionTimeMin

    tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, {"from": accounts[0]})

    # print(tx.events['LogReceipt'])
    receivedSum = tx.events['LogReceipt']['receivedWei']
    refundedSum = tx.events['LogReceipt']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 120 and refundedSum == 0    

def test_workFlow(eB, rpc, web3):
    newTest()
    _provider  = accounts[0]
    _requester = accounts[1]    

    registerProvider(eB, rpc, web3)
    registerRequester(eB, rpc, web3, _requester)                    

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
    cacheHour      = 0
    
    sourceCodeHashArray = [sourceCodeHash] # Hashed of the data file in array
    cacheHourArray      = [cacheHour]
    
    dataTransferIn  = 100
    dataTransferOut = 100
    dataTransferInArray  = [dataTransferIn]    
    dataTransfer         = [dataTransferIn, dataTransferOut]

    coreArray       = [2,   4,  2]    
    coreMinArray    = [10, 15, 20]

    storageID_list = [scripts.lib.storageID.IPFS]
    storageID_cacheType = [storageID_list, scripts.lib.cacheType.PRIVATE, eB.getProviderSetBlockNumbers(accounts[0])[-1]]

    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, _provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, eB, web3)
    
    tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                      {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print(eB.getJobInfo(_provider, jobKey, 0, 0))
    print(eB.getJobInfo(_provider, jobKey, 0, 1))
    print(eB.getJobInfo(_provider, jobKey, 0, 2))

    with pytest.reverts(): # getJobInfo should revert
        print(eB.getJobInfo(_provider, jobKey, 1, 2))
        
    # setJobStatus for the workflow: -------------
    index = 0
    jobID = 0
    startTime = 10
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    index = 0
    jobID = 1
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    receivedSum = 0
    refundedSum = 0
    
    # receiveDeposit for the workflow: -------------
    index = 0
    jobID = 0
    executionTimeMin = 10
    dataTransfer = [100, 0]
    endTime = 20
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, {"from": accounts[0]})
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']
    # --------
    index = 0
    jobID = 1
    executionTimeMin = 15
    dataTransfer = [0, 0]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, {"from": accounts[0]})
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']
    # --------
    index = 0
    jobID = 2
    executionTimeMin = 20
    dataTransfer = [0, 100]
    endTime = 39
    
    ipfsBytes32    = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    resultIpfsHash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, {"from": accounts[0]})
    # print(tx.events['LogReceipt'])
    receivedSum += tx.events['LogReceipt']['receivedWei']
    refundedSum += tx.events['LogReceipt']['refundedWei']

    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))    
    assert(jobPriceValue == receivedSum + refundedSum)

    # eB.updateDataReceivedBlock(resultIpfsHash, {"from": accounts[4]})
      
def test_submitJob(eB, rpc, web3):
    newTest()
    _provider  = accounts[0]
    _requester = accounts[1]    

    registerProvider(eB, rpc, web3)
    registerRequester(eB, rpc, web3, _requester)                    
    
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
            
            jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd" # Source Code's jobKey
            
            dataKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd" # Source Code's jobKey
            ipfsBytes32    = scripts.lib.convertIpfsToBytes32(dataKey)
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
            storageID_list = [scripts.lib.storageID.IPFS]
            
            # print(sourceCodeHashArray[0])
            jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, _provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, eB, web3)
            
            jobPriceValueSum   += jobPriceValue            
            storageID_cacheType = [storageID_list, scripts.lib.cacheType.PRIVATE, eB.getProviderSetBlockNumbers(accounts[0])[-1]]
            dataTransferInArray = [dataTransferIn]
            
            tx = eB.submitJob(_provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut,
                              storageID_cacheType, cacheHourArray, sourceCodeHashArray,
                              {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
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
            tx = eB.setJobStatusRunning(jobKey, index, jobID, int(arguments[0]), {"from": accounts[0]})
            if index == 0:
                with pytest.reverts():
                    tx = eB.setJobStatusRunning(jobKey, index, jobID, int(arguments[0])+1, {"from": accounts[0]})
                
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
            executionTimeMin = int(arguments[1]) - int(arguments[0])            
            tx = eB.receiveDeposit(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, int(arguments[1]), dataTransfer, {"from": accounts[0]})
            # sourceCodeHashArray
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
    ret = eB.getJobStorageTime(_provider, _requester, sourceCodeHash)
    print('ReceivedBlockNumber=' + str(ret[0]) + ' | ' + 'cacheDuration=' + str(ret[1] * 240) + ' | ' + 'isUsed=' + str(ret[2]))
    print('----------------------------------')
    
    print(eB.getReceiveStoragePayment(_provider, _requester, sourceCodeHash, {"from": _provider}))
    
    '''
    rpc.mine(240)
    tx = eB.receiveStoragePayment(_requester, sourceCodeHash, {"from": _provider});
    print('receiveStoragePayment => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceiveStoragePayment(_requester, sourceCodeHash, {"from": _provider}))
    print('----------------------------------') 
    '''    
    
