#!/usr/bin/env python

from imports import *

# checks: does IPFS run on the background or not
def isIpfsOn(): #{
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n') 
   if int(check) == 0:
      print("Error: IPFS does not work on the background.\nPlease run:  ipfs daemon &") 
      os.system("bash ../runIPFS.sh") 
      time.sleep(5) 
      os.system("cat ipfs.out") 
   else:
      print("IPFS is already on") 
#}

if __name__ == '__main__': #{
    if(len(sys.argv) == 8):
        clusterAddress = str(sys.argv[1]) 
        clusterAddress = web3.toChecksumAddress(clusterAddress) 
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress) 
        my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        jobKey         = str(sys.argv[2]) 
        coreNum        = int(sys.argv[3]) 
        coreMinuteGas  = int(sys.argv[5]) 
        jobDescription = str(sys.argv[4]) 
        storageType    = int(sys.argv[6]) 
        accountID      = int(sys.argv[7]) 
    else:
        # USER Inputs----------------------------------------------------------------
        clusterAddress = "0xda1e61e853bb8d63b1426295f59cb45a34425b63" 
        clusterAddress = web3.toChecksumAddress(clusterAddress) 
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.functions.getClusterInfo(clusterAddress).call() 
        my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        #jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName" 
        jobKey         = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"  #"1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG"
        coreNum        = 1 
        coreGasDay     = 0 
        coreGasHour    = 0 
        coreGasMin     = 1 
        jobDescription = "Science" 
        storageType    = 0 
        accountID      = 0 
        # ----------------------------------------------------------------------------

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call(): #{
       print("Requested cluster's Ethereum Address (" + clusterAddress + ") does not exist.")
       sys.exit() 
    #}
    
    fromAccount = web3.eth.accounts[accountID] 
    fromAccount = web3.toChecksumAddress(fromAccount) 
    if not eBlocBroker.functions.isUserExist(fromAccount).call(): #{
       print("Requested user's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit() 
    #}

    if storageType == 0 or storageType == 2: #{
       isIpfsOn() 
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress'] 
       print("Trying to connect into: " + strVal) 
       output = os.popen('ipfs swarm connect ' + strVal).read() 
       print(output)
    #}

    msgValue      = coreNum * pricePerMin * coreMinuteGas 

    if (storageType == 0 and len(jobKey) != 46) or (storageType == 2 and len(jobKey) != 46) or (storageType == 4 and len(jobKey) != 33): #{
       print("jobKey's length does not match with its original length. Please check your jobKey.")
       sys.exit() 
    #}

    gasLimit = 4500000 
    if coreNum <= coreNumber and len(jobDescription) < 128 and int(storageType) < 5 and len(jobKey) <= 64 and coreMinuteGas != 0: #{
       tx = eBlocBroker.transact({"from": web3.eth.accounts[accountID], "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription, coreMinuteGas, storageType) 
       print('Tx: ' + tx.hex()) 
    #}
#}
