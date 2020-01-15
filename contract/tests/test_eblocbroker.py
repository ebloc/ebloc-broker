#!/usr/bin/python3

import pytest
import os

import scripts.lib
from brownie import accounts

rows, columns = os.popen('stty size', 'r').read().split()
spaces = ''.join(['-'] * (int(columns)-1))

whisperPubKey = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
cwd = os.getcwd()

provider_email = "provider@gmail.com"
federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
miniLockID = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
available_core_num = 128
priceCoreMin = 1
priceDataTransfer = 1
priceStorage = 1
priceCache = 1
prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]
commitmentBlockNum = 240
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
zeroAddress = '0x0000000000000000000000000000000000000000'


def get_block_number(w3):
    print('blockNumber=' + str(w3.eth.blockNumber)  + ' | ' + 'blockNumber on contractTx=' +  str(w3.eth.blockNumber + 1))
    return w3.eth.blockNumber


def withdraw(eB, w3, address, amount):
    temp = address.balance()
    assert eB.balanceOf(address) == amount
    tx = eB.withdraw({"from": address, 'gas_price': 0})
    received = address.balance() - temp
    assert amount == received
    assert eB.balanceOf(address) == 0


def get_block_timestamp(web3):
    return web3.eth.getBlock(get_block_number(web3)).timestamp


def new_test():
    print(spaces, end="")


def register_provider(eB, rpc, web3):
    '''Register Provider'''
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    tx = eB.registerProvider(provider_email, federatedCloudID, miniLockID, available_core_num, prices, commitmentBlockNum, ipfs_address, whisperPubKey, {'from': accounts[0]})

    orcID = '0000-0001-7642-0442'
    orcID_as_bytes = str.encode(orcID)

    assert not eB.isOrcIDVerified(accounts[0]), "orcID initial value should be false"
    tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]}) # ORCID should be registered.
    assert eB.isOrcIDVerified(accounts[0]), "isOrcIDVerified is failed"

    with pytest.reverts(): # orcID should only set once for the same user
        eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]})

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
    assert eB.doesRequesterExist(_account), True

    blockReadFrom, b = eB.getRequesterInfo(_account)
    orcID = '0000-0001-7642-0552'
    orcID_as_bytes = str.encode(orcID)

    print(eB.isOrcIDVerified(_account))

    assert eB.isOrcIDVerified(_account) == False, "orcID initial value should be false"
    tx = eB.authenticateOrcID(_account, orcID_as_bytes, {'from': accounts[0]}) # ORCID should be registered.
    assert eB.isOrcIDVerified(_account), "isOrcIDVerified is failed"

    with pytest.reverts(): # orcID should only set once for the same user
        tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {'from': accounts[0]})

    blockReadFrom, b = eB.getRequesterInfo(_account)
    assert orcID == b.decode("utf-8").replace('\x00',''), "orcID set false"


# @pytest.mark.skip(reason="skip")
def test_ownership(eB):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]

    with pytest.reverts(): # transferOwnership should revert
        eB.transferOwnership('0x0000000000000000000000000000000000000000', {"from": accounts[0]})

    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]


def test_initial_balances(eB):
    assert eB.balanceOf(accounts[0]) == 0


def test_storage_refund(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    _requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, _requester)

    storageHour_list = []
    sourceCodeHash_list = []

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash_list.append(web3.toBytes(hexstr= ipfsBytes32))
    storageHour_list.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey_2)
    sourceCodeHash_list.append(web3.toBytes(hexstr= ipfsBytes32))
    storageHour_list.append(1)

    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferOut = 100
    dataTransferIn_list = [dataTransferIn_1, dataTransferIn_2]
    data_prices_set_blocknumber_list = [0, 0]

    core_list = [2]
    coreMin_list = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.StorageID.EUDAT, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PRIVATE, scripts.lib.CacheType.PUBLIC]

    args = [provider, providerPriceBlockNumber, storageID_list, cacheType_list, data_prices_set_blocknumber_list]

    data_prices_set_blocknumber_list = [0, 0]  # Provider's registered data won't be used
    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, _requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)

    jobPriceValue += 1 # for test 1 wei extra is paid
    tx = eB.submitJob(jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

    refunded = tx.events['LogJob']['refunded']
    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print('refunded=' + str(refunded))
    print(tx.events['LogJob']['jobKey'])
    withdraw(eB, web3, _requester, refunded) # check for extra payment is checked

    index = 0
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, core_list, coreMin_list, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events['LogRefundRequest']['refundedWei']
    print('refundedWei=' + str(refundedWei))
    withdraw(eB, web3, _requester, refundedWei)

    with pytest.reverts(): # VM Exception while processing transaction: invalid opcode
        call = eB.getJobInfo(provider, jobKey, 5, jobID)

    storageCostSum = 0
    for i in range(len(sourceCodeHash_list)):
        _hash = sourceCodeHash_list[i]
        storageCostSum += eB.getReceivedStorageDeposit(provider, _requester, _hash)
        # print('=' + str(eB.getReceivedStorageDeposit(provider, _requester, _hash)))

    assert cost['storageCost'] == storageCostSum
    assert (cost['computationalCost'] + cost['dataTransferCost'] + cost['cacheCost'] == refundedWei)

    rpc.mine(240)

    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events['LogStorageDeposit']['payment']
    print('refundedWei=' + str(refundedWei))
    withdraw(eB, web3, _requester, refundedWei)

    with pytest.reverts(): # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})

    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[1], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events['LogStorageDeposit']['payment']
    paidAddress = tx.events['LogStorageDeposit']['paidAddress']
    withdraw(eB, web3, _requester, refundedWei)

    with pytest.reverts(): # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})

    assert(_requester == paidAddress)
    assert eB.balanceOf(provider) == 0

    # ---------------------------------------------------------------
    print('----Same Job submitted after full refund -----')

    tx = eB.submitJob(jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list, {"from": _requester, "value": web3.toWei(jobPriceValue, "wei")})

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
    for i in range(len(sourceCodeHash_list)):
        _hash = sourceCodeHash_list[i]
        storagePayment.append(eB.getReceivedStorageDeposit(provider, _requester, _hash))

    isVerified = [True, True]
    # Called by the cluster
    eB.sourceCodeHashReceived(jobKey, index, sourceCodeHash_list, cacheType_list, isVerified, {"from": provider, "gas": 4500000})
    for i in range(len(sourceCodeHash_list)):
        print(eB.getJobStorageTime(provider, sourceCodeHash_list[i]))

    with pytest.reverts(): # refundStorageDeposit should revert, because it is already used by the provider
        for i in range(len(sourceCodeHash_list)):
            tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[i], {"from": _requester, "gas": 4500000})

    with pytest.reverts():
        tx = eB.receiveStorageDeposit(_requester, sourceCodeHash_list[0], {"from": provider, "gas": 4500000})

    print('Passing 1 hour time...')
    rpc.mine(240)
    # After deadline (1 hr) is completed to store the data, provider could obtain the money
    for i in range(len(sourceCodeHash_list)):
        tx = eB.receiveStorageDeposit(_requester, sourceCodeHash_list[i], {"from": provider, "gas": 4500000})
        amount = tx.events['LogStorageDeposit']['payment']
        withdraw(eB, web3, provider, amount)
        assert storagePayment[i] == amount


def test_updateProvider(eB, rpc, web3):
    new_test()
    rpc.mine(5)
    register_provider(eB, rpc, web3)
    federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateProviderInfo(provider_email, federatedCloudID, miniLockID, ipfs_address, whisperPubKey, {'from': accounts[0]})

    print(eB.getUpdatedProviderPricesBlocks(accounts[0]))

    available_core_num = 64
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})
    assert eB.getProviderInfo(accounts[0], eB.getUpdatedProviderPricesBlocks(accounts[0])[1])[1][0] == 64

    available_core_num = 16
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})
    assert eB.getProviderInfo(accounts[0], eB.getUpdatedProviderPricesBlocks(accounts[0])[1])[1][0] == 16

    rpc.mine(240)
    available_core_num = 32
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {'from': accounts[0]})
    assert eB.getUpdatedProviderPricesBlocks(accounts[0])[2] == 489

    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    print(str(providerPriceInfo))
    blockReadFrom = providerPriceInfo[0]
    print(blockReadFrom)
    print(eB.getUpdatedProviderPricesBlocks(accounts[0]))
    assert blockReadFrom == 249


def test_multipleData(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    requester = accounts[1]
    requester1 = accounts[2]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)
    register_requester(eB, rpc, web3, requester1)

    storageHour_list = []
    sourceCodeHash_list = []

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash_list.append(web3.toBytes(hexstr= ipfsBytes32))
    storageHour_list.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey_2)
    sourceCodeHash_list.append(web3.toBytes(hexstr= ipfsBytes32))
    storageHour_list.append(1)

    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferOut = 100
    dataTransferIn_list = [dataTransferIn_1, dataTransferIn_2]
    data_prices_set_blocknumber_list = [0, 0]  # Provider's registered data won't be used
    dataTransfer = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    core_list = [2]
    coreMin_list = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [scripts.lib.StorageID.EUDAT, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PRIVATE, scripts.lib.CacheType.PUBLIC]
    args = [provider, providerPriceBlockNumber, storageID_list, cacheType_list, data_prices_set_blocknumber_list]

    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)

    # First time job is submitted with the data files
    tx = eB.submitJob(jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, args, storageHour_list,
                      sourceCodeHash_list, {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})

    print('jobIndex=' + str(tx.events['LogJob']['index']))
    print(tx.events['LogJob']['jobKey'])
    assert cost['storageCost'] == 200, "Since it is not verified yet storageCost should be 200"

    # Second time job is wanted to send by the same user  with the same data files
    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)
    assert cost['storageCost'] == 0, "Since storageCost is already paid by the user it should be 0"

    # Second time job is wanted to send by the differnt user  with the same data files
    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester1, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)
    assert cost['storageCost'] == 200, "Since it is not verified yet storageCost should be 200"

    # => Cluster verifies the gvien data files for the related job
    index = 0
    isVerified_list = [True, True]
    tx = eB.sourceCodeHashReceived(jobKey, index, sourceCodeHash_list, cacheType_list, isVerified_list, {"from": provider, "gas": 4500000})

    # Second time job is wanted to send by the differnt user  with the same data files
    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)
    assert cost['storageCost'] == 0, "Since it is verified torageCost should be 0"


    # Second time job is wanted to send by the differnt user  with the same data files
    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester1, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)
    assert cost['storageCost'] == 100, "Since data1 is verified and publis, its  storageCost should be 0"

    receivedBlock, cacheDuration, is_private, isVerified_Used = scripts.lib.getJobStorageTime(eB, provider, sourceCodeHash_list[1], True)

    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut,
                                           storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)

    assert cost['storageCost'] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost['dataTransferCost'] == dataTransferOut, "dataTransferCost should cover only dataTransferOut"

    tx = eB.submitJob(jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list, {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})

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

    tx = eB.processPayment(jobKey, [index, jobID, end_time], execution_time_min, result_ipfs_hash, dataTransfer[0], dataTransfer[1], {"from": accounts[0]})
    receivedSum = tx.events['LogProcessPayment']['receivedWei']
    refundedSum = tx.events['LogProcessPayment']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 320 and refundedSum == 0
    withdraw(eB, web3, accounts[0], receivedSum, )
    withdraw(eB, web3, requester, refundedSum)

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

    tx = eB.processPayment(jobKey, [index, jobID, end_time], execution_time_min, result_ipfs_hash, dataTransfer[0], dataTransfer[1], {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum = tx.events['LogProcessPayment']['receivedWei']
    refundedSum = tx.events['LogProcessPayment']['refundedWei']
    print(str(receivedSum) + ' ' + str(refundedSum))
    assert receivedSum == 120 and refundedSum == 0
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)


def test_workflow(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)

    with pytest.reverts():  # getJobInfo should revert
        eB.updataDataPrice(sourceCodeHash, 20, 100, {"from": provider})

    eB.registerData(sourceCodeHash, 20, 240, {"from": provider})
    eB.removeRegisteredData(sourceCodeHash, {"from": provider})  # Should submitJob fail if it is not removed

    sourceCodeHash1 = "0x68b8d8218e730fc2957bcb12119cb204"

    # "web3.toBytes(hexstr=scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve"))
    eB.registerData(sourceCodeHash1, 20, 240, {"from": provider})
    rpc.mine(6)

    with pytest.reverts():  # registerData should revert
        eB.registerData(sourceCodeHash1, 20, 240, {"from": provider})

    eB.updataDataPrice(sourceCodeHash1, 250, 241, {"from": provider})

    print("getRegisteredDataBlockNumbers=" + str(eB.getRegisteredDataBlockNumbers(provider, sourceCodeHash1)))
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print("registerDataPrice=" + str(res))
    assert res[0] == 20

    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 253)
    print("registerDataPrice=" + str(res))
    assert res[0] == 250

    rpc.mine(231)
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print("registerDataPrice=" + str(res))
    assert res[0] == 20
    rpc.mine(1)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print("registerDataPrice=" + str(res))
    assert res[0] == 250

    sourceCodeHash_list = [sourceCodeHash, sourceCodeHash1]  # Hashed of the data file in array
    storageHour_list = [0, 0]

    dataTransferIn_list = [100, 100]
    dataTransferOut = 100

    data_prices_set_blocknumber_list = [0, 253]
    dataTransfer = [dataTransferIn_list, dataTransferOut]

    core_list = [2,   4,  2]
    coreMin_list = [10, 15, 20]

    storageID_list = [scripts.lib.StorageID.IPFS, scripts.lib.StorageID.IPFS]
    cacheType_list = [scripts.lib.CacheType.PUBLIC, scripts.lib.CacheType.PUBLIC]
    args = [provider, eB.getProviderSetBlockNumbers(accounts[0])[-1], storageID_list, cacheType_list, data_prices_set_blocknumber_list, core_list, coreMin_list]

    jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut,
                                           storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)

    # first submit
    tx = eB.submitJob(jobKey, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list, {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})

    print(eB.getJobInfo(provider, jobKey, 0, 0))
    print(eB.getJobInfo(provider, jobKey, 0, 1))
    print(eB.getJobInfo(provider, jobKey, 0, 2))

    print('-------------------')
    assert tx.events['LogRegisteredDataRequest'][0]['registeredDataHash'] == "0x0000000000000000000000000000000068b8d8218e730fc2957bcb12119cb204", "Registered Data should be used"

    with pytest.reverts(): # getJobInfo should revert
        print(eB.getJobInfo(provider, jobKey, 1, 2))
        print(eB.getJobInfo(provider, jobKey, 0, 3))

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

    receivedSum = 0
    refundedSum = 0
    tx = eB.processPayment(jobKey, [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list], execution_time_min, result_ipfs_hash, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    receivedSum = tx.events['LogProcessPayment']['receivedWei']
    refundedSum = tx.events['LogProcessPayment']['refundedWei']
    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))
    # ------------------
    index = 0
    jobID = 1
    execution_time_min = 15
    dataTransfer = [0, 0]
    end_time = 39

    ipfsBytes32 = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)

    tx = eB.processPayment(jobKey, [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list], execution_time_min, result_ipfs_hash, {"from": accounts[0]})
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

    with pytest.reverts(): # processPayment should revert, setRunning is not called for the job=2
        tx = eB.processPayment(jobKey, [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list], execution_time_min, result_ipfs_hash, {"from": accounts[0]})

    index = 0
    jobID = 2
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    tx = eB.processPayment(jobKey, [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list], execution_time_min, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum += tx.events['LogProcessPayment']['receivedWei']
    refundedSum += tx.events['LogProcessPayment']['refundedWei']
    print('receivedSum=' + str(receivedSum) + ' | ' + 'refundedSum=' + str(refundedSum) + ' | ' + 'jobPriceValue=' + str(jobPriceValue))

    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)
    assert(jobPriceValue - cost['storageCost'] == receivedSum + refundedSum)

    # eB.updateDataReceivedBlock(result_ipfs_hash, {"from": accounts[4]})


def test_submitJob(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)

    print(cwd)
    fname = cwd + '/files/test.txt'
    # fname = cwd + '/files/test_.txt'

    print('Registered provider addresses:')
    print(eB.getProviders())

    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    # blockReadFrom = providerPriceInfo[0]
    _providerPriceInfo = providerPriceInfo[1]
    # availableCoreNum = _providerPriceInfo[0]
    # commitmentBlockDuration = _providerPriceInfo[1]
    priceCoreMin = _providerPriceInfo[2]
    # priceDataTransfer = _providerPriceInfo[3]
    # priceStorage = _providerPriceInfo[4]
    # priceCache = _providerPriceInfo[5]

    print("Provider's available_core_num=" + str(available_core_num))
    print("Provider's priceCoreMin="       + str(priceCoreMin))
    print(providerPriceInfo)

    jobPriceValueSum = 0
    jobID = 0
    index = 0
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")

            storageHour = 1
            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])
            core_list = [core]
            coreMin_list = [coreMin]

            # time.sleep(1)
            # rpc.mine(int(arguments[0]))

            jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd" # Source Code's jobKey

            dataKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd" # Source Code's jobKey
            ipfsBytes32 = scripts.lib.convertIpfsToBytes32(dataKey)
            sourceCodeHash = web3.toBytes(hexstr= ipfsBytes32)
            # print("Client Balance before: " + str(web3.eth.balanceOf(account)))
            # print("Contract Balance before: " + str(web3.eth.balanceOf(accounts[0])))

            sourceCodeHash_list = [sourceCodeHash]  # Hashed of the
            storageHour_list = [storageHour]

            dataTransferIn = 100
            dataTransferOut = 100

            dataTransferIn_list = [dataTransferIn]
            data_prices_set_blocknumber_list = [0]
            storageID_list = [scripts.lib.StorageID.IPFS]
            cacheType_list = [scripts.lib.CacheType.PUBLIC]

            args = [provider, eB.getProviderSetBlockNumbers(accounts[0])[-1], storageID_list, cacheType_list, data_prices_set_blocknumber_list]

            # print(sourceCodeHash_list[0])
            jobPriceValue, cost = scripts.lib.cost(core_list, coreMin_list, provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, storageID_list, cacheType_list, data_prices_set_blocknumber_list, eB, web3)

            jobPriceValueSum += jobPriceValue
            dataTransferIn_list = [dataTransferIn]

            tx = eB.submitJob(jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list,
                              {"from": requester, "value": web3.toWei(jobPriceValue, "wei")})
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
            print('jobIndex=' + str(tx.events['LogJob']['index']))

            # print("Contract Balance after: " + str(web3.eth.balanceOf(accounts[0])))
            # print("Client Balance after: " + str(web3.eth.balanceOf(accounts[8])))
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
    ipfsBytes32 = scripts.lib.convertIpfsToBytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr= ipfsBytes32)

    index = 0
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")
            if index == 0:
                dataTransferIn = 90
                dataTransferOut = 100
            else:
                dataTransferIn = 0
                dataTransferOut = 100

            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])
            core_list = [core]
            coreMin_list = [coreMin]


            print('\nContractBalance=' + str(eB.getContractBalance()))
            dataTransfer = [dataTransferIn, dataTransferOut]
            jobID = 0
            execution_time_min = int(arguments[1]) - int(arguments[0])
            end_time = int(arguments[1])
            tx = eB.processPayment(jobKey, [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list], execution_time_min, result_ipfs_hash, {"from": accounts[0]})
            # sourceCodeHash_list
            received = tx.events['LogProcessPayment']['receivedWei']
            refunded = tx.events['LogProcessPayment']['refundedWei']
            withdraw(eB, web3, accounts[0], received)
            withdraw(eB, web3, requester, refunded)
            print('received=' + str(received) + '| refunded=' + str(refunded))
            index += 1

    print('\nContractBalance=' + str(eB.getContractBalance()))
    # Prints finalize version of the linked list.
    size = eB.getProviderReceiptSize(provider)
    for i in range(0, size):
        print(eB.getProviderReceiptNode(provider, i))

    print('----------------------------------')
    print('StorageTime for job: ' + jobKey)
    receivedBlock, cacheDuration, is_private, isVerified_Used = scripts.lib.getJobStorageTime(eB, provider, sourceCodeHash, True)

    print('receivedBlockNumber=' + str(receivedBlock) + ' | ' +
          'cacheDuration=' + str(cacheDuration * 240) + ' | ' +
          'isPrivate=' + str(is_private)              + ' | ' +
          'isVerified_Used=' + str(isVerified_Used))

    print('----------------------------------')

    print(eB.getReceivedStorageDeposit(provider, requester, sourceCodeHash, {"from": provider}))

    '''
    rpc.mine(240)
    tx = eB.receiveStorageDeposit(_requester, sourceCodeHash, {"from": provider});
    print('receiveStorageDeposit => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceivedStorageDeposit(_requester, sourceCodeHash, {"from": }))
    print('----------------------------------')
    '''
