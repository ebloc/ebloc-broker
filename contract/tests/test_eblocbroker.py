#!/usr/bin/python3

import inspect
import os
from os import path, sys
from pdb import set_trace as bp  # noqa: F401

import brownie
import scripts.lib
from brownie import accounts

import lib  # noqa: F401
import utils
from contract.scripts.lib import Job

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
    eB.withdraw({"from": address, "gas_price": 0})
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
    eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})  # ORCID should be registered.
    assert eB.isOrcIDVerified(accounts[0]), "isOrcIDVerified is failed"

    with brownie.reverts():  # orcID should only set once for the same user
        eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})

    block_read_from, b = eB.getRequesterInfo(accounts[0])
    assert orcID == b.decode("utf-8").replace("\x00", ""), "orcID set false"


def registerrequester(eB, rpc, web3, _account):
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

    block_read_from, b = eB.getRequesterInfo(_account)
    orcID = "0000-0001-7642-0552"
    orcID_as_bytes = str.encode(orcID)

    print(eB.isOrcIDVerified(_account))

    assert not eB.isOrcIDVerified(_account), "orcID initial value should be false"
    eB.authenticateOrcID(_account, orcID_as_bytes, {"from": accounts[0]})  # ORCID should be registered.
    assert eB.isOrcIDVerified(_account), "isOrcIDVerified is failed"

    with brownie.reverts():  # orcID should only set once for the same user
        eB.authenticateOrcID(accounts[0], orcID_as_bytes, {"from": accounts[0]})

    block_read_from, b = eB.getRequesterInfo(_account)
    assert orcID == b.decode("utf-8").replace("\x00", ""), "orcID set false"


def test_stored_data_usage(eB, rpc, web3):
    new_test()
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    requester_1 = accounts[2]

    register_provider(eB, rpc, web3, 100)
    registerrequester(eB, rpc, web3, requester)
    registerrequester(eB, rpc, web3, requester_1)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))

    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [1]
    job.core_execution_durations = [5]

    job.providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [lib.StorageID.GDRIVE.value, lib.StorageID.GDRIVE.value]
    job.cache_types = [lib.CacheType.PUBLIC.value, lib.CacheType.PRIVATE.value]
    args = [
        provider,
        job.providerPriceBlockNumber,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    # first time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(tx.events["LogDataStorageRequest"]["owner"])

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 2

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 0, "Since it is not verified yet storage_cost should be 2"
    assert cost["dataTransfer_cost"] == 1

    with brownie.reverts():
        job_price_revert = 500  # dataTransferIn cost is ignored
        tx = eB.submitJob(
            jobKey,
            job.dataTransferIns,
            args,
            job.storage_hours,
            job.source_code_hashes,
            {"from": requester, "value": web3.toWei(job_price_revert, "wei")},
        )

    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    assert "LogDataStorageRequest" not in tx.events
    print("Passing 1 hour time...")
    rpc.mine(241)

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    # first time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
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
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3, 100)
    registerrequester(eB, rpc, web3, requester)

    job.source_code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.cores = [1]
    job.core_execution_durations = [5]
    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1
    job.storage_ids = [lib.StorageID.EUDAT.value, lib.StorageID.EUDAT.value]
    job.cache_types = [lib.CacheType.PUBLIC.value, lib.CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    args = [
        provider,
        providerPriceBlockNumber,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]
    tx = eB.submitJob(
        job.source_code_hashes[0],
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    index = 0
    jobID = 0
    startTime = 1579524978
    tx = eB.setJobStatusRunning(job.source_code_hashes[0], index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(60)
    rpc.mine(5)

    args = [index, jobID, 1579524998, 2, 0, [1], [5], True]
    tx = eB.processPayment(job.source_code_hashes[0], args, 1, zeroBytes32, {"from": accounts[0]})
    receivedSum = tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(receivedSum) + " " + str(refundedSum))
    assert receivedSum + refundedSum == 505
    assert receivedSum == 104 and refundedSum == 401
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)


def test_storage_refund(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    registerrequester(eB, rpc, web3, requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))
    job.storage_hours.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581V"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))
    job.storage_hours.append(1)

    job.dataTransferIns = [100, 100]
    job.dataTransferOut = 100
    job.data_prices_set_block_numbers = [0, 0]

    job.cores = [2]
    job.core_execution_durations = [10]

    job.providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [lib.StorageID.EUDAT.value, lib.StorageID.IPFS.value]
    job.cache_types = [lib.CacheType.PRIVATE.value, lib.CacheType.PUBLIC.value]

    # provider's registered data won't be used
    job.data_prices_set_block_numbers = [0, 0]

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    job_price += 1  # for test 1 wei extra is paid
    args = [
        provider,
        job.providerPriceBlockNumber,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]
    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    refunded = tx.events["LogJob"]["refunded"]
    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print("refunded=" + str(refunded))
    print(tx.events["LogJob"]["jobKey"])
    withdraw(eB, web3, requester, refunded)  # check for extra payment is checked

    index = 0
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, job.cores, job.core_execution_durations, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print("refundedWei=" + str(refundedWei))
    withdraw(eB, web3, requester, refundedWei)

    with brownie.reverts():  # VM Exception while processing transaction: invalid opcode
        eB.getJobInfo(provider, jobKey, 5, jobID)

    storage_cost_sum = 0
    for source_code_hash in job.source_code_hashes:
        storage_cost_sum += eB.getReceivedStorageDeposit(provider, requester, source_code_hash)

    assert cost["storage_cost"] == storage_cost_sum
    assert cost["computational_cost"] + cost["dataTransfer_cost"] + cost["cache_cost"] == refundedWei

    rpc.mine(240)

    tx = eB.refundStorageDeposit(provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    print("refundedWei=" + str(refundedWei))
    withdraw(eB, web3, requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(
            provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000}
        )

    tx = eB.refundStorageDeposit(provider, requester, job.source_code_hashes[1], {"from": requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    paid_address = tx.events["LogStorageDeposit"]["paidAddress"]
    withdraw(eB, web3, requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = eB.refundStorageDeposit(
            provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000}
        )

    assert requester == paid_address
    assert eB.balanceOf(provider) == 0

    print("========= Same Job submitted after full refund =========")

    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(f"jobIndex={tx.events['LogJob']['index']}")
    print(tx.events["LogJob"]["jobKey"])

    index = 1
    jobID = 0
    tx = eB.refund(provider, jobKey, index, jobID, job.cores, job.core_execution_durations, {"from": provider})
    print(eB.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print("refundedWei=" + str(refundedWei))

    assert cost["computational_cost"] + cost["dataTransfer_cost"] + cost["cache_cost"] == refundedWei

    storage_cost_sum = 0
    storagePayment = []
    for source_code_hash in job.source_code_hashes:
        storagePayment.append(eB.getReceivedStorageDeposit(provider, requester, source_code_hash))

    job.isVerified = [True, True]
    # called by the cluster
    eB.sourceCodeHashReceived(
        jobKey, index, job.source_code_hashes, job.cache_types, job.isVerified, {"from": provider, "gas": 4500000}
    )

    for source_code_hash in job.source_code_hashes:
        print(eB.getJobStorageTime(provider, source_code_hash))

    with brownie.reverts():  # refundStorageDeposit should revert, because it is already used by the provider
        for source_code_hash in job.source_code_hashes:
            tx = eB.refundStorageDeposit(provider, requester, source_code_hash, {"from": requester, "gas": 4500000})

    with brownie.reverts():
        tx = eB.receiveStorageDeposit(requester, job.source_code_hashes[0], {"from": provider, "gas": 4500000})

    print("Passing 1 hour time...")
    rpc.mine(240)
    # after deadline (1 hr) is completed to store the data, provider could obtain the money
    for idx, source_code_hash in enumerate(job.source_code_hashes):
        tx = eB.receiveStorageDeposit(requester, source_code_hash, {"from": provider, "gas": 4500000})
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
    eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})
    assert eB.getProviderInfo(accounts[0], eB.getUpdatedProviderPricesBlocks(accounts[0])[1])[1][0] == 16

    print("Passing 1 hour time...")
    rpc.mine(240)
    available_core_num = 32
    eB.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})
    assert eB.getUpdatedProviderPricesBlocks(accounts[0])[2] == 489

    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    print(str(providerPriceInfo))
    block_read_from = providerPriceInfo[0]
    print(block_read_from)
    print(eB.getUpdatedProviderPricesBlocks(accounts[0]))
    assert block_read_from == 249


def test_multipleData(eB, rpc, web3):
    new_test()
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    requester_1 = accounts[2]

    register_provider(eB, rpc, web3)
    registerrequester(eB, rpc, web3, requester)
    registerrequester(eB, rpc, web3, requester_1)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey_2)
    job.source_code_hashes.append(web3.toBytes(hexstr=ipfsBytes32))

    job.dataTransferIns = [100, 100]
    job.dataTransferOut = 100
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [2]
    job.core_execution_durations = [10]
    providerPriceBlockNumber = eB.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [lib.StorageID.EUDAT.value, lib.StorageID.IPFS.value]
    job.cache_types = [lib.CacheType.PRIVATE.value, lib.CacheType.PUBLIC.value]
    args = [
        provider,
        providerPriceBlockNumber,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

    # first time job is submitted with the data files
    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert cost["storage_cost"] == 200, "Since it is not verified yet storage_cost should be 200"

    # second time job is wanted to send by the same user  with the same data files
    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3,)
    assert cost["storage_cost"] == 0, "Since storage_cost is already paid by the user it should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = scripts.lib.cost(provider, requester_1, job, eB, web3,)
    print(str(cost))
    assert cost["storage_cost"] == 200, "Since it is not verified yet storage_cost should be 200"

    # => Cluster verifies the gvien data files for the related job
    index = 0
    isVerified_list = [True, True]
    tx = eB.sourceCodeHashReceived(
        jobKey, index, job.source_code_hashes, job.cache_types, isVerified_list, {"from": provider, "gas": 4500000}
    )

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3,)
    assert cost["storage_cost"] == 0, "Since it is verified torageCost should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = scripts.lib.cost(provider, requester_1, job, eB, web3,)
    assert cost["storage_cost"] == 100, "Since data1 is verified and publis, its  storage_cost should be 0"

    # ds = scripts.lib.DataStorage(eB, provider, source_code_hashes[1], True)

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3,)

    assert cost["storage_cost"] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost["dataTransfer_cost"] == job.dataTransferOut, "dataTransfer_cost should cover only dataTransferOut"

    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))

    # provider side:
    index = 0
    jobID = 0
    startTime = get_block_timestamp(web3)
    execution_time = 10
    result_ipfs_hash = "0xabcd"
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time

    args = [
        index,
        jobID,
        end_time,
        sum(job.dataTransferIns),
        job.dataTransferOut,
        job.cores,
        job.core_execution_durations,
        False,
    ]
    tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
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
    execution_time = 10
    result_ipfs_hash = "0xabcd"
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time)
    rpc.mine(1)
    end_time = startTime + 15 * 4 * execution_time

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.core_execution_durations, False]
    tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    receivedSum = tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(receivedSum) + " " + str(refundedSum))
    assert receivedSum == 120 and refundedSum == 0
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)


def test_workflow(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    registerrequester(eB, rpc, web3, requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    ipfsBytes32 = utils.ipfs_to_bytes32(jobKey)
    sourceCodeHash = web3.toBytes(hexstr=ipfsBytes32)

    with brownie.reverts():  # getJobInfo should revert
        eB.updataDataPrice(sourceCodeHash, 20, 100, {"from": provider})

    eB.registerData(sourceCodeHash, 20, 240, {"from": provider})
    eB.removeRegisteredData(sourceCodeHash, {"from": provider})  # should submitJob fail if it is not removed

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

    job.source_code_hashes = [sourceCodeHash, sourceCodeHash1]  # Hashed of the data file in array
    job.storage_hours = [0, 0]

    job.dataTransferIns = [100, 100]
    job.dataTransferOut = 100

    job.data_prices_set_block_numbers = [0, 253]

    job.cores = [2, 4, 2]
    job.core_execution_durations = [10, 15, 20]

    job.storage_ids = [lib.StorageID.IPFS.value, lib.StorageID.IPFS.value]
    job.cache_types = [lib.CacheType.PUBLIC.value, lib.CacheType.PUBLIC.value]
    args = [
        provider,
        eB.getProviderSetBlockNumbers(accounts[0])[-1],
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]

    job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3,)

    # first submit
    tx = eB.submitJob(
        jobKey,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
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

    # setJobStatus for the workflow:
    index = 0
    jobID = 0
    startTime = 10
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    index = 0
    jobID = 1
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    # processPayment for the workflow:
    index = 0
    jobID = 0
    execution_time = 10
    dataTransfer = [100, 0]
    end_time = 20

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)

    received_sums = []
    refunded_sums = []
    receivedSum = 0
    refundedSum = 0
    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.core_execution_durations, False]
    tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price={job_price}")
    # ------------------
    index = 0
    jobID = 1
    execution_time = 15
    dataTransfer = [0, 0]
    end_time = 39

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)
    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.core_execution_durations, False]
    tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price={job_price}")

    # --------
    index = 0
    jobID = 2
    execution_time = 20
    dataTransfer = [0, 100]
    end_time = 39

    ipfsBytes32 = utils.ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    result_ipfs_hash = web3.toBytes(hexstr=ipfsBytes32)

    with brownie.reverts():  # processPayment should revert, setRunning is not called for the job=2
        args = [
            index,
            jobID,
            end_time,
            dataTransfer[0],
            dataTransfer[1],
            job.cores,
            job.core_execution_durations,
            False,
        ]
        tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    index = 0
    jobID = 2
    startTime = 20
    tx = eB.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.core_execution_durations, True]
    tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    receivedSum += tx.events["LogProcessPayment"]["receivedWei"]
    refundedSum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"receivedSum={receivedSum} | refundedSum={refundedSum} | job_price={job_price}")
    print(received_sums)
    print(refunded_sums)
    assert job_price - cost["storage_cost"] == receivedSum + refundedSum
    withdraw(eB, web3, accounts[0], receivedSum)
    withdraw(eB, web3, requester, refundedSum)
    # eB.updateDataReceivedBlock(result_ipfs_hash, {"from": accounts[4]})


def test_submitJob(eB, rpc, web3):
    new_test(inspect.stack()[0][3])
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(eB, rpc, web3)
    registerrequester(eB, rpc, web3, requester)

    fname = f"{cwd}/files/test.txt"
    # fname = cwd + '/files/test_.txt'

    print("Registered provider addresses:")
    print(eB.getProviders())

    providerPriceInfo = eB.getProviderInfo(accounts[0], 0)
    # block_read_from = providerPriceInfo[0]
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

    job_priceSum = 0
    jobID = 0
    index = 0
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip("\n").split(" ")

            storageHour = 1
            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])

            job.cores = [core]
            job.core_execution_durations = [coreMin]
            # time.sleep(1)
            # rpc.mine(int(arguments[0]))

            jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # source Code's jobKey
            dataKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # source Code's jobKey
            ipfsBytes32 = utils.ipfs_to_bytes32(dataKey)
            sourceCodeHash = web3.toBytes(hexstr=ipfsBytes32)
            # print("Client Balance before: " + str(web3.eth.balanceOf(account)))
            # print("Contract Balance before: " + str(web3.eth.balanceOf(accounts[0])))

            job.source_code_hashes = [sourceCodeHash]  # Hashed of the
            job.storage_hours = [storageHour]

            job.dataTransferIns = [100]
            job.dataTransferOut = 100
            job.data_prices_set_block_numbers = [0]
            job.storage_ids = [lib.StorageID.IPFS.value]
            job.cache_types = [lib.CacheType.PUBLIC.value]

            args = [
                provider,
                eB.getProviderSetBlockNumbers(accounts[0])[-1],
                job.storage_ids,
                job.cache_types,
                job.data_prices_set_block_numbers,
                job.cores,
                job.core_execution_durations,
                job.dataTransferOut,
            ]

            # print(source_code_hashes[0])
            job_price, cost = scripts.lib.cost(provider, requester, job, eB, web3)

            job_priceSum += job_price
            dataTransferIns = [100]

            tx = eB.submitJob(
                jobKey,
                dataTransferIns,
                args,
                job.storage_hours,
                job.source_code_hashes,
                {"from": requester, "value": web3.toWei(job_price, "wei")},
            )
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
            print("jobIndex=" + str(tx.events["LogJob"]["index"]))

            # print("Contract Balance after: " + str(web3.eth.balanceOf(accounts[0])))
            # print("Client Balance after: " + str(web3.eth.balanceOf(accounts[8])))
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(eB.getJobInfo(provider, jobKey, index, jobID))
            index += 1

    print(f"TotalPaid={job_priceSum}")
    # print(block_read_from)
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
                dataTransferIn_sum = 90
                job.dataTransferOut = 100
            else:
                dataTransferIn_sum = 0
                job.dataTransferOut = 100

            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])

            job.cores = [core]
            job.core_execution_durations = [coreMin]

            print("\nContractBalance=" + str(eB.getContractBalance()))
            jobID = 0
            execution_time = int(arguments[1]) - int(arguments[0])
            end_time = int(arguments[1])
            args = [
                index,
                jobID,
                end_time,
                dataTransferIn_sum,
                job.dataTransferOut,
                job.cores,
                job.core_execution_durations,
                True,
            ]
            tx = eB.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
            # source_code_hashes
            received = tx.events["LogProcessPayment"]["receivedWei"]
            refunded = tx.events["LogProcessPayment"]["refundedWei"]
            withdraw(eB, web3, accounts[0], received)
            withdraw(eB, web3, requester, refunded)
            print(f"received={received} | refunded={refunded}")

    print("\nContractBalance=" + str(eB.getContractBalance()))
    # prints finalize version of the linked list.
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
    tx = eB.receiveStorageDeposit(requester, sourceCodeHash, {"from": provider});
    print('receiveStorageDeposit => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(eB.getReceivedStorageDeposit(requester, sourceCodeHash, {"from": }))
    print('----------------------------------')
    """
