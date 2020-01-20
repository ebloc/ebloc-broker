#!/usr/bin/env python3

import sys
import pprint
import traceback
import lib
import owncloud

from imports import connect, connectEblocBroker, getWeb3
from contract.scripts.lib import cost
from contract.scripts.lib import convertIpfsToBytes32
from contractCalls.get_provider_info import get_provider_info


def submitJob(provider, key, core, coreMin, dataTransferIn_list, dataTransferOut, storageID_list, sourceCodeHash_list, cacheType_list, storageHour_list, accountID, jobPriceValue,
              data_prices_set_blocknumber_list, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'E: web3 is not connected'

    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(w3.eth.accounts[accountID])

    status, providerInfo = get_provider_info(provider, eBlocBroker, w3)

    providerPriceBlockNumber = eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]

    print("Provider's availableCoreNum: " + str(providerInfo['availableCoreNum']))
    print("Provider's priceCoreMin: " + str(providerInfo['priceCoreMin']))

    # my_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=providerInfo['blockReadFrom'], toBlock=providerInfo['blockReadFrom'] + 1)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        return False, "E: Requested provider's Ethereum Address \"" + provider + "\" does not registered."

    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_from).call()

    if not eBlocBroker.functions.doesRequesterExist(_from).call():
        return False, "E: Requester's Ethereum Address \"" + _from + "\" does not exist."

    if not eBlocBroker.functions.isOrcIDVerified(_from).call():
        return False, 'E: Requester\'s orcid: \"' + orcid.decode('UTF') + '\" is not verified.'

    '''
    if lib.storageID_list.IPFS == storageID_list or lib.storageID_list.IPFS_MINILOCK == storageID_list:
       lib.isIpfsOn()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress']nnn
       print('Trying to connect into ' + strVal)
       output = os.popen('ipfs swarm connect ' + strVal).read()
       if 'success' in output:
          print(output)
    '''

    '''
    print(sourceCodeHash_list[0].encode('utf-8'))
    for i in range(len(sourceCodeHash_list)):
        sourceCodeHash_list[i] = sourceCodeHash_list[i]
        if len(sourceCodeHash_list[i]) != 32 and len(sourceCodeHash_list[i]) != 0:
            return False, 'sourceCodeHash_list should be 32 characters.'
    '''
    if not sourceCodeHash_list:
        return False, 'E: sourceCodeHash list is empty.'

    if len(key) != 46 and (lib.StorageID.IPFS.value == storageID_list or lib.StorageID.IPFS_MINILOCK.value == storageID_list):
        return False,  "E: key's length does not match with its original length, it should be 46. Please check your key length"

    if len(key) != 33 and lib.StorageID.GDRIVE.value == storageID_list:
        return False, "E: key's length does not match with its original length, it should be 33. Please check your key length"

    for i in range(len(core)):
        if core[i] > providerInfo['availableCoreNum']:
            return False, "E: Requested core[" + str(i) + "], which is " + str(core[i]) + ", is greater than the provider's core number"
        if coreMin[i] == 0:
            return False, 'E: coreMin[' + str(i) +'] is provided as 0. Please provide non-zero value'

    for i in range(len(storageID_list)):
        if storageID_list[i] > 4:
            return False, 'E: Wrong storageID_list value is given. Please provide from 0 to 4'

    if len(key) >= 64:
        return False, 'E: Length of key is greater than 64, please provide lesser'

    for i in range(len(coreMin)):
        if coreMin[i] > 1440:
            return False, 'E: coreMin provided greater than 1440. Please provide smaller value'

    print(cacheType_list)

    for i in range(len(cacheType_list)):
        if cacheType_list[i] > 3:  # {0:'private', 1:'public', 2:'none', 3:'ipfs'}
            return False, 'E: cachType provided greater than 1. Please provide smaller value'

    # if len(jobDescription) >= 128:
    #    return 'Length of jobDescription is greater than 128, please provide lesser.'
    args = [provider, providerPriceBlockNumber, storageID_list, cacheType_list, data_prices_set_blocknumber_list, core, coreMin]

    try:
        gasLimit = 4500000
        print(sourceCodeHash_list)
        tx = eBlocBroker.functions.submitJob(key, dataTransferIn_list, dataTransferOut, args, storageHour_list, sourceCodeHash_list).transact({"from": _from, "value": jobPriceValue, "gas": gasLimit})
    except Exception:
        return False, traceback.format_exc()

    return True, str(tx.hex())


if __name__ == '__main__':
    w3 = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    if len(sys.argv) == 10:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        core = int(sys.argv[3])
        coreMin = int(sys.argv[4])
        dataTransfer = int(sys.argv[5])
        storageID_list = int(sys.argv[6])
        sourceCodeHash = str(sys.argv[7])
        storageHour_list = int(sys.argv[8])
        accountID = int(sys.argv[9])
    elif len(sys.argv) == 13:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        core = int(sys.argv[3])
        coreDayDuration = int(sys.argv[4])
        coreHour = int(sys.argv[5])
        coreMin = int(sys.argv[6])
        dataTransferIn = int(sys.argv[7])
        dataTransferOut = int(sys.argv[8])
        storageID_list = int(sys.argv[9])
        sourceCodeHash = str(sys.argv[10])
        storageHour_list = int(sys.argv[11])
        accountID = int(sys.argv[12])
        coreMin = coreMin + coreHour * 60 + coreDayDuration * 1440
        dataTransfer = dataTransferIn + dataTransferOut
    else:
        # ================================================ REQUESTER Inputs for testing ================================================
        storageID_list = lib.StorageID.IPFS.value
        _provider =  w3.toChecksumAddress('0x57b60037b82154ec7149142c606ba024fbb0f991')  # netlab
        cacheType_list = lib.CacheType.PRIVATE.value  # default
        storageHour_list = []
        sourceCodeHash_list = []
        coreMin_list = []

        if storageID_list == lib.StorageID.IPFS.value: # IPFS
            print('Submitting through IPFS...')
            key = 'QmbL46fEH7iaccEayKpS9FZnkPV5uss4SFmhDDvbmkABUJ'  # 30 seconds job
            coreDayDuration = 0
            coreHour = 0
            coreMin = 1
            coreMin = coreMin + coreHour * 60 + coreDayDuration * 1440
            coreMin_list.append(coreMin)

            # DataSourceCodes:
            ipfsBytes32 = convertIpfsToBytes32(key)
            sourceCodeHash_list.append(w3.toBytes(hexstr= ipfsBytes32))
            storageHour_list.append(1)

            ipfsBytes32 = convertIpfsToBytes32('QmSYzLDW5B36jwGSkU8nyfHJ9xh9HLjMsjj7Ciadft9y65')  # data1/data.txt
            sourceCodeHash_list.append(w3.toBytes(hexstr= ipfsBytes32))
            storageHour_list.append(1)
            cacheType_list = lib.CacheType.PUBLIC.value  # default
        elif storageID_list == lib.StorageID.EUDAT.value:
            print('Submitting through EUDAT...')
            oc = owncloud.Client('https://b2drop.eudat.eu/')
            with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
                password = content_file.read().strip()

            oc.login(lib.OC_USER_ID, password)
            sourceCodeHash = '00000000000000000000000000000000'
        elif storageID_list == lib.StorageID.GITHUB.value:
            print('Submitting through GitHub...')
            key = "avatar-lavventura=simpleSlurmJob"
            coreDayDuration = 0
            coreHour = 0
            coreMin = 1
            sourceCodeHash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

        core_list = [1]
        dataTransferIn_list = [1, 1]
        dataTransferOut = 1
        dataTransfer = [dataTransferIn_list, dataTransferOut]
        accountID = 0

    requester = w3.toChecksumAddress(w3.eth.accounts[accountID])
    jobPriceValue, cost = cost(core_list, coreMin_list, _provider, requester, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, storageHour_list, eBlocBroker, w3, False)

    status, result = submitJob(_provider, key, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, storageID_list,
                               sourceCodeHash_list, cacheType_list, storageHour_list, accountID, jobPriceValue, eBlocBroker, w3)

    if not status:
        print(result)
        sys.exit()
    else:
        print('tx_hash=' + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt['status'])
        if receipt['status'] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args['index']))
            except IndexError:
                print('Transaction is reverted.')
