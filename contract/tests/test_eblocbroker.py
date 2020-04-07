#!/usr/bin/python3

import inspect
import os
from os import path, sys
from pdb import set_trace as bp  # noqa: F401

import brownie
from brownie import accounts

import lib  # noqa: F401
import scripts.lib
import utils

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

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
zeroAddress = "0x0000000000000000000000000000000000000000"
zeroBytes32 = "0x00"


def get_block_number(w3):
    print(f"blockNumber={w3.eth.blockNumber} | blockNumber on contractTx={w3.eth.blockNumber + 1}")
    return w3.eth.blockNumber


def withdraw(eB, w3, address, amount):
    temp = address.balance()
    assert eB.balanceOf(address) == amount
    tx = eB.withdraw({"from": address, "gas_price": 0})
    received = address.balance() - temp
    assert amount == received
    assert eB.balanceOf(address) == 0


def get_block_timestamp(web3):
    return web3.eth.getBlock(get_block_number(web3)).timestamp


def new_test(name=""):
    print("\x1b[6;30;42m" + name + "============================================================" + "\x1b[0m")


def register_provider(eB, rpc, web3, priceCoreMin=1):
    """Register Provider"""
    rpc.mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    tx = eB.registerProvider(
        provider_email,
        federatedCloudID,
        miniLockID,
        available_core_num,
        prices,
        commitmentBlockNum,
        ipfs_address,
        whisperPubKey,
        {"from": accounts[0]},
    )

    orcID = "0000-0001-7642-0442"
    orcID_as_bytes = str.encode(orcID)

    assert not eB.isOrcIDVerified(accounts[0]), "orcID initial value should be false"
    tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})  # ORCID should be registered.
    assert eB.isOrcIDVerified(accounts[0]), "isOrcIDVerified is failed"

    with brownie.reverts():  # orcID should only set once for the same user
        eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})

    blockReadFrom, b = eB.getRequesterInfo(accounts[0])
    assert orcID == b.decode("utf-8").replace("\x00", ""), "orcID set false"


def register_requester(eB, rpc, web3, _account):
    """Register Requester"""
    tx = eB.registerRequester(
        "email@gmail.com",
        "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
        "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ",
        "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
        "ebloc",
        whisperPubKey,
        {"from": _account},
    )
    assert eB.doesRequesterExist(_account), True

    blockReadFrom, b = eB.getRequesterInfo(_account)
    orcID = "0000-0001-7642-0552"
    orcID_as_bytes = str.encode(orcID)

    print(eB.isOrcIDVerified(_account))

    assert eB.isOrcIDVerified(_account) == False, "orcID initial value should be false"
    tx = eB.authenticateOrcID(_account, orcID_as_bytes, {"from": accounts[0]})  # ORCID should be registered.
    assert eB.isOrcIDVerified(_account), "isOrcIDVerified is failed"

    with brownie.reverts():  # orcID should only set once for the same user
        tx = eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})

    blockReadFrom, b = eB.getRequesterInfo(_account)
    assert orcID == b.decode("utf-8").replace("\x00", ""), "orcID set false"


def test_stored_data_usage(eB, rpc, web3):
    new_test()
    provider = accounts[0]
    requester = accounts[1]
    requester1 = accounts[2]

    register_provider(eB, rpc, web3, 100)
    register_requester(eB, rpc, web3, requester)
    register_requester(eB, rpc, web3, requester1)

    storage_hour_list = []
    sourceCodeHash_list = []

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))

    dataTransferIn_1 = 1
    dataTransferIn_2 = 1
    dataTransferOut = 1
    dataTransferIn_list = [dataTransferIn_1, dataTransferIn_2]
    # Provider's registered data won't be used
    storage_hour_list = [1, 1]
    data_prices_set_blocknumber_list = [0, 0]
    data_transfer = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    core_list = [1]
    coreMin_list = [5]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [lib.StorageID.GDRIVE.value, lib.StorageID.GDRIVE.value]
    cacheType_list = [lib.CacheType.PUBLIC.value, lib.CacheType.PRIVATE.value]
    args = [
        provider,
        providerPriceBlockNumber,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        core_list,
        coreMin_list,
        dataTransferOut,
    ]

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    # First time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print(tx.events["LogDataStorageRequest"]["owner"])

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 2

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 0, "Since it is not verified yet storage_cost should be 2"
    assert cost["dataTransfer_cost"] == 1

    with brownie.reverts():
        job_price_value_revert = 500  # dataTransferIn cost is ignored
        tx = eB.submitJob(
            jobKey,
            dataTransferIn_list,
            args,
            storage_hour_list,
            sourceCodeHash_list,
            {"from": requester, "value": web3.toWei(job_price_value_revert, "wei")},
        )

    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    assert "LogDataStorageRequest" not in tx.events
    print("Passing 1 hour time...")
    rpc.mine(241)

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    # First time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print(tx.events["LogDataStorageRequest"]["owner"])


# @pytest.mark.skip(reason="skip")
def test_ownership(eB):
    """Get Owner"""
    assert eB.getOwner() == accounts[0]

    with brownie.reverts():  # transferOwnership should revert
        eB.transferOwnership("0x0000000000000000000000000000000000000000", {"from": accounts[0]})

    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]


def test_initial_balances(eB):
    assert eB.balanceOf(accounts[0]) == 0


def test_computational_refund(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3, 100)
    register_requester(eB, rpc, web3, requester)

    sourceCodeHash_list = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]

    core_list = [1]
    coreMin_list = [5]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storageID_list = [lib.StorageID.EUDAT.value, lib.StorageID.EUDAT.value]
    cacheType_list = [lib.CacheType.PUBLIC.value, lib.CacheType.PUBLIC.value]
    storageHour_list = [0, 0]
    data_prices_set_blocknumber_list = [0, 0]
    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storageHour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    args = [
        provider,
        providerPriceBlockNumber,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        core_list,
        coreMin_list,
        dataTransferOut,
    ]
    tx = eB.submitJob(
        sourceCodeHash_list[0],
        dataTransferIn_list,
        args,
        storageHour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    index = 0
    jobID = 0
    startTime = 1579524978
    tx = eB.setJobStatusRunning(sourceCodeHash_list[0], index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(60)
    rpc.mine(5)

    args = [index, jobID, 1579524998, 2, 0, [1], [5], True]
    tx = eB.processPayment(sourceCodeHash_list[0], args, 1, zeroBytes32, {"from": accounts[0]})
    receivedSum = tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(receivedSum) + " " + str(refundedSum))
    assert receivedSum + refundedSum == 505
    assert receivedSum == 104 and refundedSum == 401
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)


def test_storage_refund(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    provider = accounts[0]
    _requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, _requester)

    storageHour_list = []
    sourceCodeHash_list = []

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))
    storageHour_list.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581V"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))
    storageHour_list.append(1)

    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferIn_list = [dataTransferIn_1, dataTransferIn_2]
    dataTransferOut = 100
    data_prices_set_blocknumber_list = [0, 0]

    core_list = [2]
    coreMin_list = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [lib.StorageID.EUDAT.value, lib.StorageID.IPFS.value]
    cacheType_list = [lib.CacheType.PRIVATE.value, lib.CacheType.PUBLIC.value]

    # Provider's registered data won't be used
    data_prices_set_blocknumber_list = [0, 0]

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        _requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storageHour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    job_price_value += 1  # for test 1 wei extra is paid
    args = [
        provider,
        providerPriceBlockNumber,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        core_list,
        coreMin_list,
        dataTransferOut,
    ]
    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storageHour_list,
        sourceCodeHash_list,
        {"from": _requester, "value": web3.toWei(job_price_value, "wei")},
    )

    refunded = tx.events["LogJob"]["refunded"]
    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print("refunded=" + str(refunded))
    print(tx.events["LogJob"]["jobKey"])
    withdraw(eB, web3, _requester, refunded)  # check for extra payment is checked

    index = 0
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, core_list, coreMin_list, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print("refundedWei=" + str(refundedWei))
    withdraw(eB, web3, _requester, refundedWei)

    with brownie.reverts():  # VM Exception while processing transaction: invalid opcode
        call = eB.getJobInfo(provider, jobKey, 5, jobID)

    storage_cost_sum = 0
    for source_code_hash in sourceCodeHash_list:
        storage_cost_sum += eB.getReceivedStorageDeposit(provider, _requester, source_code_hash)

    assert cost["storage_cost"] == storage_cost_sum
    assert cost["computational_cost"] + cost["dataTransfer_cost"] + cost["cache_cost"] == refundedWei

    rpc.mine(240)

    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    print("refundedWei=" + str(refundedWei))
    withdraw(eB, web3, _requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})

    tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[1], {"from": _requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    paidAddress = tx.events["LogStorageDeposit"]["paidAddress"]
    withdraw(eB, web3, _requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(provider, _requester, sourceCodeHash_list[0], {"from": _requester, "gas": 4500000})

    assert _requester == paidAddress
    assert eB.balanceOf(provider) == 0

    # ---------------------------------------------------------------
    print("----Same Job submitted after full refund -----")

    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storageHour_list,
        sourceCodeHash_list,
        {"from": _requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print(f"jobIndex={tx.events['LogJob']['index']}")
    print(tx.events["LogJob"]["jobKey"])

    index = 1
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, core_list, coreMin_list, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print("refundedWei=" + str(refundedWei))

    assert cost["computational_cost"] + cost["dataTransfer_cost"] + cost["cache_cost"] == refundedWei

    storage_cost_sum = 0
    storagePayment = []
    for source_code_hash in sourceCodeHash_list:
        storagePayment.append(eB.getReceivedStorageDeposit(provider, _requester, source_code_hash))

    isVerified = [True, True]
    # Called by the cluster
    eB.sourceCodeHashReceived(
        jobKey, index, sourceCodeHash_list, cacheType_list, isVerified, {"from": provider, "gas": 4500000}
    )

    for source_code_hash in sourceCodeHash_list:
        print(eB.getJobStorageTime(provider, source_code_hash))

    with brownie.reverts():  # refundStorageDeposit should revert, because it is already used by the provider
        for source_code_hash in sourceCodeHash_list:
            tx = eB.refundStorageDeposit(provider, _requester, source_code_hash, {"from": _requester, "gas": 4500000})

    with brownie.reverts():
        tx = eB.receiveStorageDeposit(_requester, sourceCodeHash_list[0], {"from": provider, "gas": 4500000})

    print("Passing 1 hour time...")
    rpc.mine(240)
    # After deadline (1 hr) is completed to store the data, provider could obtain the money
    for idx, source_code_hash in enumerate(sourceCodeHash_list):
        tx = eB.receiveStorageDeposit(_requester, source_code_hash, {"from": provider, "gas": 4500000})
        amount = tx.events["LogStorageDeposit"]["payment"]
        withdraw(eB, web3, provider, amount)
        assert storagePayment[idx] == amount


def test_updateProvider(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    rpc.mine(5)
    register_provider(eB, rpc, web3)
    federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = eB.updateProviderInfo(
        provider_email, federatedCloudID, miniLockID, ipfs_address, whisperPubKey, {"from": accounts[0]}
    )

    print(eB.getUpdatedProviderPricesBlocks(accounts[0]))

    available_core_num = 64
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})
    assert eB.getProviderInfo(accounts[0], eB.getUpdatedProviderPricesBlocks(accounts[0])[1])[1][0] == 64

    available_core_num = 16
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})
    assert eB.getProviderInfo(accounts[0], eB.getUpdatedProviderPricesBlocks(accounts[0])[1])[1][0] == 16

    print("Passing 1 hour time...")
    rpc.mine(240)
    available_core_num = 32
    tx = eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})
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

    storage_hour_list = []
    sourceCodeHash_list = []

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    sourceCodeHash_list.append(web3.toBytes(hexstr=ipfsBytes32))

    dataTransferIn_1 = 100
    dataTransferIn_2 = 100
    dataTransferOut = 100
    dataTransferIn_list = [dataTransferIn_1, dataTransferIn_2]
    # Provider's registered data won't be used
    storage_hour_list = [1, 1]
    data_prices_set_blocknumber_list = [0, 0]
    data_transfer = [(dataTransferIn_1 + dataTransferIn_2), dataTransferOut]

    core_list = [2]
    coreMin_list = [10]

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    storageID_list = [lib.StorageID.EUDAT.value, lib.StorageID.IPFS.value]
    cacheType_list = [lib.CacheType.PRIVATE.value, lib.CacheType.PUBLIC.value]
    args = [
        provider,
        providerPriceBlockNumber,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        core_list,
        coreMin_list,
        dataTransferOut,
    ]

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    # First time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 200, "Since it is not verified yet storage_cost should be 200"

    # Second time job is wanted to send by the same user  with the same data files
    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )
    assert cost["storage_cost"] == 0, "Since storage_cost is already paid by the user it should be 0"

    # Second time job is wanted to send by the differnt user  with the same data files
    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester1,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )
    print(str(cost))
    assert cost["storage_cost"] == 200, "Since it is not verified yet storage_cost should be 200"

    # => Cluster verifies the gvien data files for the related job
    index = 0
    isVerified_list = [True, True]
    tx = eB.sourceCodeHashReceived(
        jobKey, index, sourceCodeHash_list, cacheType_list, isVerified_list, {"from": provider, "gas": 4500000}
    )

    # Second time job is wanted to send by the differnt user  with the same data files
    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )
    assert cost["storage_cost"] == 0, "Since it is verified torageCost should be 0"

    # Second time job is wanted to send by the differnt user  with the same data files
    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester1,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )
    assert cost["storage_cost"] == 100, "Since data1 is verified and publis, its  storage_cost should be 0"

    # ds = scripts.lib.DataStorage(eB, provider, sourceCodeHash_list[1], True)

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    assert cost["storage_cost"] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost["dataTransfer_cost"] == dataTransferOut, "dataTransfer_cost should cover only dataTransferOut"

    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))

    # Provider Side:--------------------
    index = 0
    jobID = 0
    startTime = get_block_timestamp(web3)
    execution_time_min = 10
    result_ipfs_hash = "0xabcd"
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time_min)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time_min

    args = [index, jobID, end_time, data_transfer[0], data_transfer[1], core_list, coreMin_list, False]
    tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})
    receivedSum = tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum = tx.events["LogProcessPayment"]["refundedWei"]
    print(f"{receivedSum} {refundedSum}")
    assert receivedSum == 320 and refundedSum == 0
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)

    dataTransferIn = 0  # already requested on index==0
    dataTransferOut = 100
    dataTransfer = [dataTransferIn, dataTransferOut]

    index = 1
    jobID = 0
    startTime = get_block_timestamp(web3)
    execution_time_min = 10
    result_ipfs_hash = "0xabcd"
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time_min)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time_min

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, False]
    tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum = tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(receivedSum) + " " + str(refundedSum))
    assert receivedSum == 120 and refundedSum == 0
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)


def test_workflow(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr=ipfsBytes32)

    with brownie.reverts():  # getJobInfo should revert
        eB.updataDataPrice(sourceCodeHash, 20, 100, {"from": provider})

    eB.registerData(sourceCodeHash, 20, 240, {"from": provider})
    eB.removeRegisteredData(sourceCodeHash, {"from": provider})  # Should submitJob fail if it is not removed

    sourceCodeHash1 = "0x68b8d8218e730fc2957bcb12119cb204"

    # "web3.toBytes(hexstr=utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve"))
    eB.registerData(sourceCodeHash1, 20, 240, {"from": provider})
    rpc.mine(6)

    with brownie.reverts():  # registerData should revert
        eB.registerData(sourceCodeHash1, 20, 240, {"from": provider})

    eB.updataDataPrice(sourceCodeHash1, 250, 241, {"from": provider})

    print(f"getRegisteredDataBlockNumbers={eB.getRegisteredDataBlockNumbers(provider, sourceCodeHash1)}")
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print(f"registerDataPrice={res}")
    assert res[0] == 20

    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 253)
    print(f"registerDataPrice={res}")
    assert res[0] == 250

    rpc.mine(231)
    get_block_number(web3)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print(f"registerDataPrice={res}")
    assert res[0] == 20
    rpc.mine(1)
    res = eB.getRegisteredDataPrice(provider, sourceCodeHash1, 0)
    print(f"registerDataPrice={res}")
    assert res[0] == 250

    sourceCodeHash_list = [sourceCodeHash, sourceCodeHash1]  # Hashed of the data file in array
    storage_hour_list = [0, 0]

    dataTransferIn_list = [100, 100]
    dataTransferOut = 100

    data_prices_set_blocknumber_list = [0, 253]
    dataTransfer = [dataTransferIn_list, dataTransferOut]

    core_list = [2, 4, 2]
    coreMin_list = [10, 15, 20]

    storageID_list = [lib.StorageID.IPFS.value, lib.StorageID.IPFS.value]
    cacheType_list = [lib.CacheType.PUBLIC.value, lib.CacheType.PUBLIC.value]
    args = [
        provider,
        eB.getProviderSetBlockNumbers(accounts[0])[-1],
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        core_list,
        coreMin_list,
        dataTransferOut,
    ]

    job_price_value, cost = scripts.lib.cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        sourceCodeHash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eB,
        web3,
    )

    # first submit
    tx = eB.submitJob(
        jobKey,
        dataTransferIn_list,
        args,
        storage_hour_list,
        sourceCodeHash_list,
        {"from": requester, "value": web3.toWei(job_price_value, "wei")},
    )

    print(eB.getJobInfo(provider, jobKey, 0, 0))
    print(eB.getJobInfo(provider, jobKey, 0, 1))
    print(eB.getJobInfo(provider, jobKey, 0, 2))

    print("-------------------")
    assert (
        tx.events["LogRegisteredDataRequestToUse"][0]["registeredDataHash"]
        == "0x0000000000000000000000000000000068b8d8218e730fc2957bcb12119cb204"
    ), "Registered Data should be used"

    with brownie.reverts():  # getJobInfo should revert
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

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)

    receivedSum_list = []
    refundedSum_list = []
    receivedSum = 0
    refundedSum = 0
    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, False]
    tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    receivedSum_list.append(tx.events["LogProcessPayment"]["receivedWei"])
    refundedSum_list.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price_value={job_price_value}")
    # ------------------
    index = 0
    jobID = 1
    execution_time_min = 15
    dataTransfer = [0, 0]
    end_time = 39

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)
    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, False]
    tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})
    receivedSum_list.append(tx.events["LogProcessPayment"]["receivedWei"])
    refundedSum_list.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price_value={job_price_value}")

    # --------
    index = 0
    jobID = 2
    execution_time_min = 20
    dataTransfer = [0, 100]
    end_time = 39

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)

    with brownie.reverts():  # processPayment should revert, setRunning is not called for the job=2
        args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, False]
        tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})

    index = 0
    jobID = 2
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, True]
    tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum_list.append(tx.events["LogProcessPayment"]["receivedWei"])
    refundedSum_list.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price_value={job_price_value}")
    print(receivedSum_list)
    print(refundedSum_list)
    assert job_price_value - cost["storage_cost"] == receivedSum + refundedSum
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)
    # eB.updateDataReceivedBlock(result_ipfs_hash, {"from": accounts[4]})


def test_submitJob(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    register_requester(eB, rpc, web3, requester)

    fname = f"{cwd}/files/test.txt"
    # fname = cwd + '/files/test_.txt'

    print("Registered provider addresses:")
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
    print("Provider's priceCoreMin=" + str(priceCoreMin))
    print(providerPriceInfo)

    job_price_valueSum = 0
    jobID = 0
    index = 0
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip("\n").split(" ")

            storageHour = 1
            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])
            core_list = [core]
            coreMin_list = [coreMin]

            # time.sleep(1)
            # rpc.mine(int(arguments[0]))

            jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # Source Code's jobKey

            dataKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # Source Code's jobKey
            ipfsBytes32 = utils.ipfs_to_bytes32(dataKey)
            sourceCodeHash = web3.toBytes(hexstr=ipfsBytes32)
            # print("Client Balance before: " + str(web3.eth.balanceOf(account)))
            # print("Contract Balance before: " + str(web3.eth.balanceOf(accounts[0])))

            sourceCodeHash_list = [sourceCodeHash]  # Hashed of the
            storage_hour_list = [storageHour]

            dataTransferIn = 100
            dataTransferOut = 100

            dataTransferIn_list = [dataTransferIn]
            data_prices_set_blocknumber_list = [0]
            storageID_list = [lib.StorageID.IPFS.value]
            cacheType_list = [lib.CacheType.PUBLIC.value]

            args = [
                provider,
                eB.getProviderSetBlockNumbers(accounts[0])[-1],
                storageID_list,
                cacheType_list,
                data_prices_set_blocknumber_list,
                core_list,
                coreMin_list,
                dataTransferOut,
            ]

            # print(sourceCodeHash_list[0])
            job_price_value, cost = scripts.lib.cost(
                core_list,
                coreMin_list,
                provider,
                requester,
                sourceCodeHash_list,
                dataTransferIn_list,
                dataTransferOut,
                storage_hour_list,
                storageID_list,
                cacheType_list,
                data_prices_set_blocknumber_list,
                eB,
                web3,
            )

            job_price_valueSum += job_price_value
            dataTransferIn_list = [dataTransferIn]

            tx = eB.submitJob(
                jobKey,
                dataTransferIn_list,
                args,
                storage_hour_list,
                sourceCodeHash_list,
                {"from": requester, "value": web3.toWei(job_price_value, "wei")},
            )
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
            print("jobIndex=" + str(tx.events["LogJob"]["index"]))

            # print("Contract Balance after: " + str(web3.eth.balanceOf(accounts[0])))
            # print("Client Balance after: " + str(web3.eth.balanceOf(accounts[8])))
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(eB.getJobInfo(provider, jobKey, index, jobID))
            index += 1

    print(f"TotalPaid={job_price_valueSum}")
    # print(blockReadFrom)
    # rpc.mine(100)
    # print(web3.eth.blockNumber)

    jobID = 0
    with open(fname) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
            tx = eB.setJobStatusRunning(jobKey, index, jobID, int(arguments[0]), {"from": accounts[0]})
            if index == 0:
                with brownie.reverts():
                    tx = eB.setJobStatusRunning(jobKey, index, jobID, int(arguments[0]) + 1, {"from": accounts[0]})

    print("----------------------------------")
    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)

    with open(fname) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
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

            print("\nContractBalance=" + str(eB.getContractBalance()))
            dataTransfer = [dataTransferIn, dataTransferOut]
            jobID = 0
            execution_time_min = int(arguments[1]) - int(arguments[0])
            end_time = int(arguments[1])
            args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], core_list, coreMin_list, True]
            tx = eB.processPayment(jobKey, args, execution_time_min, result_ipfs_hash, {"from": accounts[0]})
            # sourceCodeHash_list
            received = tx.events["LogProcessPayment"]["receivedWei"]
            refunded = tx.events["LogProcessPayment"]["refundedWei"]
            withdraw(eB, web3, accounts[0], received)
            withdraw(eB, web3, requester, refunded)
            print(f"received={received} | refunded={refunded}")

    print("\nContractBalance=" + str(eB.getContractBalance()))
    # Prints finalize version of the linked list.
    size = eB.getProviderReceiptSize(provider)
    for idx in range(0, size):
        print(eB.getProviderReceiptNode(provider, idx))

    print("----------------------------------")
    print(f"StorageTime for job: {jobKey}")
    ds = scripts.lib.DataStorage(eB, web3, provider, sourceCodeHash, True)

    print(
        f"receivedBlockNumber={ds.received_block} | storage_duration(block numbers)={ds.storage_duration} | is_private={ds.is_private} | isVerified_Used={ds.is_verified_used}"
    )
    print("----------------------------------")

    print(eB.getReceivedStorageDeposit(provider, requester, sourceCodeHash, {"from": provider}))
    print("\x1b[6;30;42m" + "DONE============================================================" + "\x1b[0m")

    """
    rpc.mine(240)
    tx = eB.receiveStorageDeposit(_requester, sourceCodeHash, {"from": provider});
    print('receiveStorageDeposit => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceivedStorageDeposit(_requester, sourceCodeHash, {"from": }))
    print('----------------------------------')
    """
