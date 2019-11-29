#!/usr/bin/python3

import pytest
import os

import scripts.lib    
from brownie import accounts

rows, columns = os.popen('stty size', 'r').read().split()
spaces = ''.join(['-'] * (int(columns)-1))

whisperPubKey = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
cwd           = os.getcwd()

provider_email = "provider@gmail.com"
federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
miniLockID = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
available_core_num = 128
priceCoreMin = 1
priceDataTransfer = 1
priceStorage = 1
priceCache = 1
prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]
commitmentBlockNum = 10
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
zeroAddress = '0x0000000000000000000000000000000000000000'


def get_block_number(w3):
    print('blockNumber=' + str(w3.eth.blockNumber)  + ' | ' + 'blockNumber on contractTx=' +  str(w3.eth.blockNumber + 1))
    return w3.eth.blockNumber


def get_block_timestamp(web3):
    return web3.eth.getBlock(get_block_number(web3)).timestamp


def new_test():
    print(spaces, end = "")

    
# @pytest.mark.skip(reason="skip")    
def test_ownership(eB):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]
    
    with pytest.reverts(): # transferOwnership should revert
        eB.transferOwnership('0x0000000000000000000000000000000000000000', {"from": accounts[0]})

    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]   

    
def test_storage_refund(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    _requester = accounts[1]    

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, _requester)                        
    
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
        
    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferOut = 100
    dataTransferInArray = [dataTransferIn_1, dataTransferIn_2]
    data_prices_set_blocknumber_array = [0, 0]
    dataTransfer = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]
    
    coreArray = [2]    
    coreMinArray = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.StorageID.EUDAT, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PRIVATE, scripts.lib.CacheType.PUBLIC]
    storageID_cacheType = [storageID_list, cacheType_list, providerPriceBlockNumber, data_prices_set_blocknumber_array]

    data_prices_set_blocknumber_array = [0, 0]  # Provider's registered data won't be used
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray,
                                           storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)

    tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])

    index = 0
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events['LogRefundRequest']['refundedWei']
    print('refundedWei=' + str(refundedWei))

    storageCostSum = 0
    for i in range(len(sourceCodeHashArray)):
        _hash = sourceCodeHashArray[i]
        storageCostSum += eB.getReceivedStorageDeposit(provider, _requester, _hash)
        # print('=' + str(eB.getReceivedStorageDeposit(provider, _requester, _hash)))

    assert cost['storageCost'] == storageCostSum
    assert (cost['computationalCost'] + cost['dataTransferCost'] + cost['cacheCost'] == refundedWei)
     
    rpc.mine(240)
    
    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events['LogStorageDeposit']['payment']
    print('refundedWei=' + str(refundedWei))

    with pytest.reverts(): # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})

    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHashArray[1], {"from": _requester, "gas": 4500000})
    refundedWei += tx.events['LogStorageDeposit']['payment']
    paidAddress = tx.events['LogStorageDeposit']['paidAddress']
        
    with pytest.reverts(): # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHashArray[0], {"from": _requester, "gas": 4500000})

    assert(cost['storageCost'] == refundedWei)
    assert(_requester == paidAddress)
    assert(eB.getProviderReceivedAmount(provider) == 0)

    # ---------------------------------------------------------------
    print('----Same Job submitted after full refund -----')

    tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])

    index = 1
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events['LogRefundRequest']['refundedWei']
    print('refundedWei=' + str(refundedWei))
    
    assert (cost['computationalCost'] + cost['dataTransferCost'] + cost['cacheCost'] == refundedWei)
    
    storageCostSum = 0
    storagePayment = []
    for i in range(len(sourceCodeHashArray)):
        _hash = sourceCodeHashArray[i]
        storagePayment.append(eB.getReceivedStorageDeposit(provider, _requester, _hash))

    isVerified = [True, True]
    # Called by the cluster
    eB.sourceCodeHashReceived(jobKey, index, sourceCodeHashArray, cacheType_list, isVerified, {"from": provider, "gas": 4500000})
    for i in range(len(sourceCodeHashArray)):
        print(eB.getJobStorageTime(provider, _requester, sourceCodeHashArray[i]))      

    with pytest.reverts(): # refundStorageDeposit should revert, because it is already used by the provider
        for i in range(len(sourceCodeHashArray)):
            tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHashArray[i], {"from": _requester, "gas": 4500000})
        
    with pytest.reverts():
        tx = eB.receiveStorageDeposit(_requester, sourceCodeHashArray[0], {"from": provider, "gas": 4500000})

    print('Passing 1 hour time...')
    rpc.mine(240)    
    # After deadline (1 hr) is completed to store the data, provider could obtain the money    
    for i in range(len(sourceCodeHashArray)):
        tx = eB.receiveStorageDeposit(_requester, sourceCodeHashArray[i], {"from": provider, "gas": 4500000})
        assert storagePayment[i] == tx.events['LogStorageDeposit']['payment']
        
    
def register_provider(eB, rpc, web3):
    '''Register Provider'''
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    tx = eB.registerProvider(provider_email, federatedCloudID, miniLockID, available_core_num, prices, commitmentBlockNum, ipfs_address, whisperPubKey, {'from': accounts[0]})

    orcID = '0000-0001-7642-0442'
    orcID_as_bytes = str.encode(orcID)

    tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]}) # ORCID should be registered.
    assert eB.isOrcIDVerified(accounts[0]), "isOrcIDVerified is failed"

    with pytest.reverts(): # orcID should only set once for the same user
        tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]})

    blockReadFrom, b = eB.getRequesterInfo(accounts[0])
    assert orcID == b.decode("utf-8").replace('\x00',''), "orcID set false"

    
def register_requester(eB, rpc, web3, _account):
    '''Register Requester'''
    tx = eB.registerRequester("email@gmail.com",
                              "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
                              "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ",
                              "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
                              'ebloc',
                              whisperPubKey, {'from': _account})
    assert eB.isRequesterExists(_account), True
    
    blockReadFrom, b = eB.getRequesterInfo(_account)
    orcID = '0000-0001-7642-0552'
    orcID_as_bytes = str.encode(orcID)

    tx = eB.authenticateOrcID(_account, orcID_as_bytes, {'from': accounts[0]}) # ORCID should be registered.    
    assert eB.isOrcIDVerified(_account), "isOrcIDVerified is failed"
    
    with pytest.reverts(): # orcID should only set once for the same user
        tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]})

    blockReadFrom, b = eB.getRequesterInfo(_account)
    assert orcID == b.decode("utf-8").replace('\x00',''), "orcID set false"

    
def test_updateProvider(eB, rpc, web3):
    new_test()
    rpc.mine(5)
    register_provider(eB, rpc, web3)

    federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateProviderInfo(provider_email, federatedCloudID, miniLockID, ipfs_address, whisperPubKey, {'from': accounts[0]})
    
    available_core_num = 64
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})
    available_core_num = 16
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})

    rpc.mine(16)
    available_core_num = 32
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})

    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    blockReadFrom = providerPriceInfo[0]
    print(blockReadFrom)
    # assert blockReadFrom == 20
    print(eB.getProviderSetBlockNumbers(accounts[0]))
        
    
def test_multipleData(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    requester = accounts[1]
    requester1 = accounts[2]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)
    register_requester(eB, rpc, web3, requester1)                       
    
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
        
    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferOut = 100
    dataTransferInArray = [dataTransferIn_1, dataTransferIn_2]
    data_prices_set_blocknumber_array = [0, 0]  # Provider's registered data won't be used
    dataTransfer = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    coreArray = [2]    
    coreMinArray = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.StorageID.EUDAT, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PRIVATE, scripts.lib.CacheType.PUBLIC]
    storageID_cacheType = [storageID_list, cacheType_list, providerPriceBlockNumber, data_prices_set_blocknumber_array]
    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut,
                                           cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)

    # First time job is submitted with the data files
    tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray,
                      sourceCodeHashArray, {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])    
    assert cost['storageCost'] == 200, "Since it is not verified yet storageCost should be 200"

    # Second time job is wanted to send by the same user  with the same data files    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)
    assert cost['storageCost'] == 0, "Since storageCost is already paid by the user it should be 0"

    # Second time job is wanted to send by the differnt user  with the same data files    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester1, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)   
    assert cost['storageCost'] == 200, "Since it is not verified yet storageCost should be 200"
        
    # => Cluster verifies the gvien data files for the related job
    index = 0
    isVerifiedArray = [True, True]
    tx = eB.sourceCodeHashReceived(jobKey, index, sourceCodeHashArray, cacheType_list, isVerifiedArray, {"from": provider})

    # Second time job is wanted to send by the differnt user  with the same data files    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)   
    assert cost['storageCost'] == 0, "Since it is verified torageCost should be 0"

    
    # Second time job is wanted to send by the differnt user  with the same data files    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester1, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)   
    assert cost['storageCost'] == 100, "Since data1 is verified and publis, its  storageCost should be 0"

    
    assert cost['storageCost'] == 9999, "Since it is verified torageCost should be 0"
    
    receivedBlock, cacheDuration, is_private, isVerified_Used = scripts.lib.getJobStorageTime(eB, provider, requester, sourceCodeHashArray[1])
    
    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut,
                                           cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)

    assert cost['storageCost'] == 0, "Since it is paid on first job submittion it should be 0"    
    assert cost['dataTransferCost'] == dataTransferOut, "dataTransferCost should cover only dataTransferOut"
    
    tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray,
                      sourceCodeHashArray, {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))

    # Provider Side:--------------------
    index = 0
    jobID = 0
    startTime = get_block_timestamp(web3)
    execution_time_min = 10
    result_ipfs_hash = '0xabcd'
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time_min)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time_min

    tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, {"from": accounts[0]})

    receivedSum = tx.events['LogProcessPayment']['receivedWei']
    refundedSum = tx.events['LogProcessPayment']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 320 and refundedSum == 0
   
    dataTransferIn = 0  # already requested on index==0
    dataTransferOut = 100
    dataTransfer = [dataTransferIn, dataTransferOut]

    index = 1
    jobID = 0
    startTime = get_block_timestamp(web3)
    execution_time_min = 10
    result_ipfs_hash = '0xabcd'
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time_min)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time_min

    tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum = tx.events['LogProcessPayment']['receivedWei']
    refundedSum = tx.events['LogProcessPayment']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 120 and refundedSum == 0    

    
def test_workflow(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    _requester = accounts[1]    

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, _requester)                   

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
    
    with pytest.reverts():  # getJobInfo should revert
        eB.updataDataPrice(sourceCodeHash, 20, 100, {"from": provider})
   
    eB.registerData(sourceCodeHash, 20, 100, {"from": provider})
    eB.removeRegisteredData(sourceCodeHash, {"from": provider}) #  Should submitJob fail if it is not removed
    
    sourceCodeHash1 = web3.toBytes(hexstr= scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve"))    
    eB.registerData(sourceCodeHash1, 20, 10, {"from": provider})
    rpc.mine(6)
    
    with pytest.reverts():  # registerData should revert
        eB.registerData(sourceCodeHash1, 20, 10, {"from": provider})
        
    eB.updataDataPrice(sourceCodeHash1, 250, 11, {"from": provider})

    print("getRegisteredDataBlockNumbers=" + str(eB.getRegisteredDataBlockNumbers(provider, sourceCodeHash1)))
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print("registerDataPrice=" + str(res))
    assert res[0] == 20

    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 23)
    assert res[0] == 250
    
    rpc.mine(1)
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print("registerDataPrice=" + str(res))
    assert res[0] == 250
        
    sourceCodeHashArray = [sourceCodeHash, sourceCodeHash1]  # Hashed of the data file in array
    cacheHourArray = [0, 0]
    
    dataTransferInArray = [100, 100]
    dataTransferOut = 100

    # getRegisteredDataPrice()
    
    data_prices_set_blocknumber_array = [0, 23] 
    dataTransfer = [dataTransferInArray, dataTransferOut]

    coreArray = [2,   4,  2]    
    coreMinArray = [10, 15, 20]

    storageID_list = [scripts.lib.StorageID.IPFS, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PUBLIC, scripts.lib.CacheType.PUBLIC]
    storageID_cacheType = [storageID_list, cacheType_list, eB.getProviderSetBlockNumbers(accounts[0])[-1], data_prices_set_blocknumber_array]

    jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut,
                                           cacheHourArray, storageID_list, cacheType_list, data_prices_set_blocknumber_array, eB, web3)
    
    tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    print(eB.getJobInfo(provider, jobKey, 0, 0))
    print(eB.getJobInfo(provider, jobKey, 0, 1))
    print(eB.getJobInfo(provider, jobKey, 0, 2))

    with pytest.reverts(): # getJobInfo should revert
        print(eB.getJobInfo(provider, jobKey, 1, 2))
        print(eB.getJobInfo(provider, jobKey, 0, 3))

    receivedSum = 0
    refundedSum = 0

    # setJobStatus for the workflow: -------------
    index = 0
    jobID = 0
    startTime = 10
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    index = 0
    jobID = 1
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    # processPayment for the workflow: -------------       
    index = 0
    jobID = 0
    execution_time_min = 10
    dataTransfer = [100, 0]
    end_time = 20
    
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    receivedSum += tx.events['LogProcessPayment']['receivedWei']
    refundedSum += tx.events['LogProcessPayment']['refundedWei']
    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))    
    # ------------------
    index = 0
    jobID = 1
    execution_time_min = 15
    dataTransfer = [0, 0]
    end_time = 39
    
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, {"from": accounts[0]})
    receivedSum += tx.events['LogProcessPayment']['receivedWei']
    refundedSum += tx.events['LogProcessPayment']['refundedWei']
    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))    
    # --------
    index = 0
    jobID = 2
    execution_time_min = 20
    dataTransfer = [0, 100]
    end_time = 39
    
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    receivedSum += tx.events['LogProcessPayment']['receivedWei']
    refundedSum += tx.events['LogProcessPayment']['refundedWei']

    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))    
    assert(jobPriceValue - cost['storageCost'] == receivedSum + refundedSum)

    # eB.updateDataReceivedBlock(result_ipfs_hash, {"from": accounts[4]})

    
def test_submitJob(eB, rpc, web3):
    new_test()
    provider  = accounts[0]
    _requester = accounts[1]    

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, _requester)                    
    
    print(cwd)
    fname = cwd + '/files/test.txt'
    # fname = cwd + '/files/test_.txt'

    print('Registered provider addresses:')
    print(eB.getProviders())
    
    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    blockReadFrom = providerPriceInfo[0]
    _providerPriceInfo = providerPriceInfo[1]
    availableCoreNum = _providerPriceInfo[0]
    commitmentBlockDuration = _providerPriceInfo[1]
    priceCoreMin = _providerPriceInfo[2]
    priceDataTransfer = _providerPriceInfo[3]
    priceStorage = _providerPriceInfo[4]
    priceCache = _providerPriceInfo[5]   
    
    print("Provider's available_core_num=" + str(available_core_num))
    print("Provider's priceCoreMin="       + str(priceCoreMin))
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
            ipfsBytes32 = scripts.lib.convertIpfsToBytes32(dataKey)
            sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
            
			# print("Client Balance before: " + str(web3.eth.getBalance(account)))
			# print("Contract Balance before: " + str(web3.eth.getBalance(accounts[0])))

            coreArray = [core]            
            coreMinArray = [coreMin]
            
            sourceCodeHashArray = [sourceCodeHash]  # Hashed of the
            cacheHourArray = [cacheHour]
            
            dataTransferIn = 100
            dataTransferOut = 100

            dataTransferInArray = [dataTransferIn]
            data_prices_set_blocknumber_array = [0]
            storageID_list = [scripts.lib.StorageID.IPFS]
            cacheType_list = [scripts.lib.CacheType.PUBLIC]

            storageID_cacheType = [storageID_list, cacheType_list, eB.getProviderSetBlockNumbers(accounts[0])[-1], data_prices_set_blocknumber_array]

            # print(sourceCodeHashArray[0])
            jobPriceValue, cost = scripts.lib.cost(coreArray, coreMinArray, provider, _requester, sourceCodeHashArray, dataTransferInArray, dataTransferOut, cacheHourArray, storageID_list, cacheType_list, eB, web3)
            
            jobPriceValueSum   += jobPriceValue
            dataTransferInArray = [dataTransferIn]
            
            tx = eB.submitJob(provider, jobKey, coreArray, coreMinArray, dataTransferInArray, dataTransferOut, storageID_cacheType, cacheHourArray, sourceCodeHashArray, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))            
            print('jobIndex=' + str(tx.events['LogJob']['index']))
            
			# print("Contract Balance after: " + str(web3.eth.getBalance(accounts[0])))
			# print("Client Balance after: " + str(web3.eth.getBalance(accounts[8])))				
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(eB.getJobInfo(provider, jobKey, index, jobID))
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
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)
    
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
            execution_time_min = int(arguments[1]) - int(arguments[0])            
            tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, int(arguments[1]), dataTransfer, {"from": accounts[0]})
            # sourceCodeHashArray
            received = tx.events['LogProcessPayment']['receivedWei']
            refunded = tx.events['LogProcessPayment']['refundedWei']
            print('received=' + str(received) + '| refunded=' + str(refunded))           
            index += 1

    print('\nContractBalance=' + str(eB.getContractBalance()))
    # Prints finalize version of the linked list.
    size = eB.getProviderReceiptSize(provider)
    for i in range(0, size):
        print(eB.getProviderReceiptNode(provider, i))

    print('----------------------------------')
    print('StorageTime for job: ' + jobKey)
    receivedBlock, cacheDuration, is_private, isVerified_Used = scripts.lib.getJobStorageTime(eB, provider, _requester, sourceCodeHash)
    
    print('receivedBlockNumber=' + str(receivedBlock) + ' | ' +
          'cacheDuration=' + str(cacheDuration * 240) + ' | ' +
          'isPrivate=' + str(is_private)              + ' | ' +
          'isVerified_Used=' + str(isVerified_Used))
    
    print('----------------------------------')
    
    print(eB.getReceivedStorageDeposit(provider, _requester, sourceCodeHash, {"from": provider}))
    
    '''
    rpc.mine(240)
    tx = eB.receiveStorageDeposit(_requester, sourceCodeHash, {"from": provider});
    print('receiveStorageDeposit => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceivedStorageDeposit(_requester, sourceCodeHash, {"from": }))
    print('----------------------------------') 
    '''    
    
