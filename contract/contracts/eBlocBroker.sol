/*
file:   eBlocBroker.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.4.17;
//pragma experimental ABIEncoderV2;
import "./Lib.sol";
import "./eBlocBrokerInterface.sol";

/* Contract Address: 0x */
/// @title eBlocBroker is a blockchain based autonomous computational resource
///        broker.
contract eBlocBroker is eBlocBrokerInterface {

    Lib.Storage private store;
    
    using Lib for Lib.intervalNode;
    using Lib for Lib.clusterData;
    using Lib for Lib.userData;
    using Lib for Lib.status;
    using Lib for Lib.Storage;
    using Lib for Lib.jobStateCodes;

    /* Following function is executed at initialization. It sets contract's deployed 
       block number and the owner of the contract. 
    */
    function eBlocBroker() public //constructor() public
    {
	store.deployedBlockNumber = block.number;
	store.owner = msg.sender; /* msg.sender is owner of the smart contract */
    }
 
    modifier isClusterExists() {
	require(store.clusterContract[msg.sender].blockReadFrom != 0);
	_ ;
    }

    modifier isBehindBlockTimeStamp(uint time) {
	require(time <= block.timestamp);
	_ ;
    }
	
    modifier deregisterClusterCheck() {
	require(store.clusterContract[msg.sender].blockReadFrom != 0 &&
		store.clusterContract[msg.sender].isRunning);
	_ ;
    }
    
    modifier checkStateID(uint8 stateID) {
	require(stateID > 2 && stateID <= 15); /*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call */
	_ ;
    }

    modifier isOwner(address addr) {
	require(addr == store.owner);
	_ ;
    }

    modifier isOrcIDverified(address userAddress) {
	require(bytes(store.userContract[userAddress].orcID).length == 0);
	_ ;
    }

    modifier isClusterRegistered() {
	require(store.clusterContract[msg.sender].blockReadFrom == 0);
	_ ;
    }

    /*
    modifier isZero(uint32 input) {
	require(input != 0);
	_ ;
    }

    modifier check_gasCoreMin_storageID(uint32 gasCoreMin, uint8 storageID) {
	// gasCoreMin is maximum 1 day 
	require(storageID < 5 && !(gasCoreMin == 0 || gasCoreMin > 1440)); 
	_ ;
    }
    */

    /* Refund funds the complete amount to client if requested job is still in the pending state or
       is not completed one hour after its required time.
       If the job is in the running state, it triggers LogRefund event on the blockchain, 
       which will be caught by the cluster in order to cancel the job. 
    */
    function refund(address clusterAddress, string memory jobKey, uint32 index) public
	returns (bool)
    {
	/* If 'clusterAddress' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = store.clusterContract[clusterAddress].jobStatus[jobKey][index];

	if (msg.sender != job.jobOwner ||
	    job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED))
	    revert();

	if (job.status == uint8(Lib.jobStateCodes.PENDING) || /* If job have not been started running*/
	   (job.status == uint8(Lib.jobStateCodes.RUNNING) && (block.timestamp - job.startTime) > job.gasCoreMin * 60 + 3600)) /* Job status remain running after one hour that job should have completed */
	    {
		msg.sender.transfer(job.received);
		job.status = uint8(Lib.jobStateCodes.REFUNDED); /* Prevents double spending */
		/*emit*/ LogRefund(clusterAddress, jobKey, index); /* scancel log */
		return true;
	    }
	else if (job.status == uint8(Lib.jobStateCodes.RUNNING)){
	    job.status = uint8(Lib.jobStateCodes.CANCELLED);
	    /*emit*/ LogRefund(clusterAddress, jobKey, index); /* scancel log */
	    return true;
	}
	else
	    revert();
    }

    function authenticateOrcID(address userAddress, string memory orcID) isOwner(msg.sender) isOrcIDverified(userAddress) public
	returns (bool success)
    {
	store.userContract[userAddress].orcID = orcID;
	return true;
    }

    /* Following function is a general-purpose mechanism for performing payment withdrawal
       by the cluster provider and paying of unused core, cache, and dataTransfer usage cost 
       back to the client
    */
    function receiptCheck(string memory jobKey,
			  uint32 index,
			  uint32 jobExecutionTimeMin,
			  bytes32 resultIpfsHash,
			  uint8 storageID,
			  uint32 endTime,
			  uint dataTransferIn,
			  uint dataTransferSum) /*isBehindBlockTimeStamp(endTime)*/ public
    /*returns (bool success)*/
    {
	require(endTime <= block.timestamp);
	/* If "msg.sender" is not mapped on 'clusterContract' array  or its "jobKey" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes 
	*/
	Lib.status      storage job = store.clusterContract[msg.sender].jobStatus[jobKey][index];	
	Lib.clusterInfo memory  info = store.clusterContract[msg.sender].info[job.clusterUpdatedBlockNumber];

	require(jobExecutionTimeMin <= job.gasCoreMin);      // Cluster cannot request more time of the job that is already requested
	require(dataTransferSum     <= job.dataTransferSum); // Cluster cannot request more than the job's given dataTransferSum amount
	
	uint amountToGain = 0;
	if (job.dataTransferIn != 0) {
	    require(dataTransferIn <= job.dataTransferIn); // Cluster cannot request more dataTransferIn that is already requested
	    amountToGain += info.priceCache * dataTransferIn; //cacheCost   
	}
	
	amountToGain +=
	    info.priceCoreMin * job.core * jobExecutionTimeMin + // computationalCost       	    
	    info.priceDataTransfer * (dataTransferSum);    // dataTransferCost	
	
	if (amountToGain > job.received ||
	    job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED))
	    revert();


	//uint32(endTime) + uint64(uint64(info.availableCoreNum) << 32);
	    
	if (!store.clusterContract[msg.sender].receiptList.receiptCheck(job, uint32(endTime) + uint64(uint64(info.availableCoreNum) << 32))) {
	    job.status = uint8(Lib.jobStateCodes.REFUNDED); /* Important to check already refunded job or not */	    
	    job.jobOwner.transfer(job.received); /* Pay back newOwned(job.received) to the client, full refund */

	    /*emit*/ LogReceipt(msg.sender, jobKey, index, job.jobOwner, 0, job.received, block.timestamp,
				resultIpfsHash, storageID, dataTransferIn, dataTransferSum);
	    return;// false; 
	}

	if (job.status == uint8(Lib.jobStateCodes.CANCELLED))
	    job.status = uint8(Lib.jobStateCodes.REFUNDED);  /* Prevents double spending */
	else    
	    job.status = uint8(Lib.jobStateCodes.COMPLETED); /* Prevents double spending */
	
	store.clusterContract[msg.sender].receivedAmount += amountToGain;	
	msg.sender.transfer(amountToGain); /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(job.received - amountToGain); /* Unused core and bandwidth is refundedn back to the client */

	/*emit*/ LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (job.received - amountToGain), block.timestamp, resultIpfsHash, storageID, dataTransferIn, dataTransferSum);
	return; // true; 
    }
        
    function receiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) isClusterExists() public	
	returns (bool success) {
	Lib.clusterData storage cluster = store.clusterContract[msg.sender];	
	
	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum < block.number) {
	    msg.sender.transfer(cluster.receivedAmountForStorage[jobOwner][sourceCodeHash]); //storagePayment
	    /*emit*/ LogStoragePayment(msg.sender, cluster.receivedAmountForStorage[jobOwner][sourceCodeHash]);	    
	    cluster.receivedAmountForStorage[jobOwner][sourceCodeHash] = 0;
	    return true;
	}
	return false;
    }
    
    /*
    function extentStorageTime(address clusterAddress, string memory sourceCodeHash, uint gasStorageHour) public
	returns (bool success) {
	require(gasStorageHour != 0);
	Lib.clusterData storage cluster = store.clusterContract[msg.sender];

	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum >= block.number) {
	    cluster.jobSt[sourceCodeHash].gasStorageBlockNum += gasStorageHour * 240;
	}
    }
    */

    /* Registers a provider's (msg.sender's) cluster to eBlocBroker */
    function registerCluster(string memory clusterEmail,
			     string memory federatedCloudID,
			     string memory miniLockID,
			     uint32 availableCoreNum,
			     uint priceCoreMin,
			     uint priceDataTransfer,
			     uint priceStorage,
			     uint priceCache,			     
			     string memory ipfsAddress,
			     string memory whisperPublicKey) public isClusterRegistered()
	returns (bool success)
    {
	require(availableCoreNum != 0 && priceCoreMin != 0 && priceDataTransfer != 0);
	
	Lib.clusterData storage cluster = store.clusterContract[msg.sender];
	
	require(!cluster.isRunning);
	cluster.info[block.number] = Lib.clusterInfo({
                	availableCoreNum:   availableCoreNum,
                        priceCoreMin:       priceCoreMin,
                        priceDataTransfer:  priceDataTransfer,
                        priceStorage:       priceStorage,
                        priceCache:         priceCache			
			});	
	store.clusterUpdatedBlockNumber[msg.sender].push(block.number);

	if (cluster.blockReadFrom != 0 && !cluster.isRunning) {
	    store.clusterAddresses[cluster.clusterAddressesID] = msg.sender;
	    cluster.blockReadFrom = block.number;
	    cluster.isRunning = true;
	} else {
	    cluster.clusterAddressesID = uint32(store.clusterAddresses.length);
	    cluster.constructCluster();
	    store.clusterAddresses.push(msg.sender); // In order to obtain the list of clusters 
	}

	/*emit*/ LogCluster(msg.sender, availableCoreNum, clusterEmail, federatedCloudID, miniLockID,
			    priceCoreMin, priceDataTransfer, priceStorage, priceCache,
			    ipfsAddress, whisperPublicKey);

	return true;
    }

    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates userData */
    function registerUser(string memory userEmail,
			  string memory federatedCloudID,
			  string memory miniLockID,
			  string memory ipfsAddress,
			  string memory githubUserName,
			  string memory whisperPublicKey) public 
	returns (bool success)
    {
	store.userContract[msg.sender].blockReadFrom = block.number;
	//store.userContract[msg.sender].orcID = orcID; //delete
	/*emit*/ LogUser(msg.sender, userEmail, federatedCloudID, miniLockID, ipfsAddress, githubUserName, whisperPublicKey);
	return true;
    }

    /* Locks the access to the Cluster. Only cluster owner could stop it */
    function deregisterCluster() public
	returns (bool success)
    {
	delete store.clusterAddresses[store.clusterContract[msg.sender].clusterAddressesID];
	store.clusterContract[msg.sender].isRunning = false; /* Cluster wont accept any more jobs */
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateCluster(string memory clusterEmail,
			   string memory federatedCloudID,
			   string memory miniLockID,
			   uint32 availableCoreNum,
			   uint priceCoreMin,
			   uint priceDataTransfer,
			   uint priceStorage,
			   uint priceCache,			     
			   string memory ipfsAddress,
			   string memory whisperPublicKey)
	public returns (bool success)
    {
	Lib.clusterData storage cluster = store.clusterContract[msg.sender];
	if (cluster.blockReadFrom == 0 || cluster.info[block.number].availableCoreNum != 0)
	    revert();

	cluster.info[block.number] = Lib.clusterInfo({
                	availableCoreNum:   availableCoreNum,
                        priceCoreMin:       priceCoreMin,
                        priceDataTransfer:  priceDataTransfer,
                        priceStorage:       priceStorage,
                        priceCache:         priceCache			
			});	
	store.clusterUpdatedBlockNumber[msg.sender].push(block.number);
	cluster.blockReadFrom = block.number;

	/*emit*/ LogCluster(msg.sender, availableCoreNum, clusterEmail, federatedCloudID, miniLockID,
			    priceCoreMin, priceDataTransfer, priceStorage, priceCache,
			    ipfsAddress, whisperPublicKey);
	return true;
    }
    
    /* Performs a job submission to eBlocBroker by a client */
    function submitJob(address /*payable*/ clusterAddress,
		       string memory jobKey,
		       uint32 core,
		       uint32 gasCoreMin,
		       uint32 dataTransferIn,
		       uint32 dataTransferOut,
		       uint8 storageID,
		       bytes32 sourceCodeHash,
		       uint8 cacheType,
		       uint gasStorageHour) /*check_gasCoreMin_storageID(gasCoreMin, storageID) isZero(core)*/ public payable
    //returns (bool success)
    {

 	Lib.clusterData storage cluster = store.clusterContract[clusterAddress];	
	uint[] memory clusterInfo = store.clusterUpdatedBlockNumber[clusterAddress];
	Lib.clusterInfo memory info = cluster.info[clusterInfo[clusterInfo.length-1]];
		
	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum > block.number){
	    if (cluster.receivedAmountForStorage[msg.sender][sourceCodeHash] != 0)
		dataTransferIn = 0;
	}
	else
	    dataTransferOut = dataTransferIn + dataTransferOut;
	
	if (core == 0 || msg.value == 0 || !cluster.isRunning || storageID > 4 || gasCoreMin == 0 ||
	    gasCoreMin > 1440 || // gasCoreMin is maximum 1 day
	    msg.value < info.priceCoreMin      * core * gasCoreMin +                // computationalCost
	                info.priceDataTransfer * dataTransferOut +                  // dataTransferCost  
	                info.priceStorage      * dataTransferIn * gasStorageHour +  // storageCost
	              	info.priceCache        * dataTransferIn                     // cacheCost
	    ||
	    sourceCodeHash.length != 32 ||
	    bytes(jobKey).length > 255  || // Max length is 255 for the filename 
	    !isUserExist(msg.sender)    ||
	    bytes(store.userContract[msg.sender].orcID).length == 0 ||
	    core > info.availableCoreNum)
	    revert();
	
	cluster.jobStatus[jobKey].push(Lib.status({
      		        status:          uint8(Lib.jobStateCodes.PENDING),
			core:            core, /* Requested core value */
			gasCoreMin:      gasCoreMin,
			dataTransferIn:  dataTransferIn,
			dataTransferSum: dataTransferOut,
			jobOwner:        msg.sender,
			received:        msg.value,
			startTime:       0,
			clusterUpdatedBlockNumber: clusterInfo[clusterInfo.length-1]
			}
		));
	
	// User can only update the job's gasStorageHour if previously set storeage time is completed
	if (gasStorageHour != 0 &&
	    cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum < block.number) {

	    if (cluster.receivedAmountForStorage[msg.sender][sourceCodeHash] != 0) {
		clusterAddress.transfer(cluster.receivedAmountForStorage[msg.sender][sourceCodeHash]); //storagePayment
		/*emit*/ LogStoragePayment(clusterAddress, cluster.receivedAmountForStorage[msg.sender][sourceCodeHash]);	    
	    }
	    
	    cluster.jobSt[sourceCodeHash].receivedBlocNumber = block.number;
	    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
	    cluster.jobSt[sourceCodeHash].gasStorageBlockNum = gasStorageHour * 240;	   
	    cluster.receivedAmountForStorage[msg.sender][sourceCodeHash] = info.priceStorage * dataTransferIn * gasStorageHour;	    
	}
	
	/*emit*/ LogJob(clusterAddress, jobKey, cluster.jobStatus[jobKey].length - 1, storageID, sourceCodeHash,
			dataTransferOut, cacheType, gasStorageHour);
	return; //true
    }

    function updateJobReceivedBlocNumber(bytes32 sourceCodeHash) public
	returns (bool success)
    {
	Lib.clusterData storage cluster = store.clusterContract[msg.sender]; //Only cluster can update receied job only to itself
	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber != 0)
 	    cluster.jobSt[sourceCodeHash].receivedBlocNumber = block.number; //Cluster only update the block.number	}
	return true;
    }
    	
    /**
     *@dev Sets requested job's description.
     *@param clusterAddress The address of the cluster.
     *@param jobKey The string of the jobKey.
     *@param index The index of the job.
     */
    function setJobDescription(address clusterAddress, string memory jobKey, string memory jobDesc) public
	returns (bool success)
    {
	if (msg.sender == store.clusterContract[clusterAddress].jobStatus[jobKey][0].jobOwner)
	    /*emit*/ LogJobDescription(clusterAddress, jobKey, jobDesc);
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(string memory jobKey, uint32 index, uint8 stateID, uint32 startTime)
	isBehindBlockTimeStamp(startTime)
	checkStateID(stateID) public
	returns (bool success)
    {
	Lib.status storage job = store.clusterContract[msg.sender].jobStatus[jobKey][index]; /* Used as a pointer to a storage */
	if (job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED)  ||
	    job.status == uint8(Lib.jobStateCodes.RUNNING)) /* Cluster can sets job's status as RUNNING and its startTime only one time */
	    revert();
	job.status = stateID;
	if (stateID == uint8(Lib.jobStateCodes.RUNNING))
	    job.startTime = startTime;

	/*emit*/ LogSetJob(msg.sender, jobKey, index, startTime);
	return true;
    }

    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* Returns the enrolled user's
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event.
       It takes Ethereum address of the user (userAddress), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address userAddress) public view
	returns(uint, string memory)
    {
	if (store.userContract[userAddress].blockReadFrom != 0)
	    return (store.userContract[userAddress].blockReadFrom, store.userContract[userAddress].orcID);
    }

    /* Returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses */
    function getClusterInfo(address clusterAddress) public view
	returns(uint, uint, uint, uint, uint, uint)
    {	
	if (store.clusterContract[clusterAddress].blockReadFrom != 0) {
	    uint[] memory clusterInfo = store.clusterUpdatedBlockNumber[clusterAddress];
	    
	    return (store.clusterContract[clusterAddress].blockReadFrom,
		    store.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].availableCoreNum,
		    store.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceCoreMin,
		    store.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceDataTransfer,
		    store.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceStorage,
		    store.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceCache);
	}
	else
	    return (0, 0, 0, 0, 0, 0);
    }

    /* Returns various information about the submitted job such as the hash of output files generated by IPFS,
       UNIX timestamp on job's start time, received Wei value from the client etc. 
    */
    function getJobInfo(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, address)
    {
	uint arrayLength = store.clusterContract[clusterAddress].jobStatus[jobKey].length;
        if (arrayLength == 0)
	    return (0, 0, 0, 0, 0, address(0x0));
	
        if (arrayLength <= index)
	    return (0, 0, 0, 0, 0, address(0x0));
	
	Lib.status memory job = store.clusterContract[clusterAddress].jobStatus[jobKey][index];
	//Lib.clusterInfo memory clusterInfo =  store.clusterContract[clusterAddress].info[job.clusterUpdatedBlockNumber];
	    
	return (job.status, job.core, job.startTime, job.received, job.gasCoreMin, job.jobOwner);
    }
    
    function getClusterPricesForJob(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.status memory job = store.clusterContract[clusterAddress].jobStatus[jobKey][index];
	Lib.clusterInfo memory clusterInfo = store.clusterContract[clusterAddress].info[job.clusterUpdatedBlockNumber];
	    
	return (clusterInfo.priceCoreMin,
		clusterInfo.priceDataTransfer,
		clusterInfo.priceStorage,
		clusterInfo.priceCache
		);
    }

    /* Returns a list of registered/updated cluster's block number */     
    function getClusterPricesBlockNumbers(address clusterAddress) public view
	returns (uint[] memory)
    {
	return store.clusterUpdatedBlockNumber[clusterAddress];
    }

    /* Returns the contract's deployed block number */
    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return store.deployedBlockNumber;
    }

    /* Returns the owner of the contract */
    function getOwner() public view
	returns (address)
    {
	return store.owner;
    }

    function getJobSize(address clusterAddress, string memory jobKey) public view
	returns (uint)

    {
	if (store.clusterContract[msg.sender].blockReadFrom == 0)
	    revert();
	return store.clusterContract[clusterAddress].jobStatus[jobKey].length;
    }

    /* Returns cluster provider's earned money amount in Wei.
       It takes a cluster's Ethereum address (clusterAddress) as parameter. 
    */
    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint)
    {
	return store.clusterContract[clusterAddress].receivedAmount;
    }
	
    /* Returns a list of registered cluster Ethereum addresses */
    function getClusterAddresses() public view
	returns (address[] memory)
    {
	return store.clusterAddresses;
    }
	
    function getJobStorageTime(address clusterAddress, bytes32 sourceCodeHash) public view
	returns(uint, uint)
    {
	Lib.clusterData storage cluster = store.clusterContract[clusterAddress];
	return (cluster.jobSt[sourceCodeHash].receivedBlocNumber,
		cluster.jobSt[sourceCodeHash].gasStorageBlockNum / 240);
    }

    /* Checks whether or not the given Ethereum address of the provider (clusterAddress) 
       is already registered in eBlocBroker. 
    */
    function isClusterExist(address clusterAddress) public view
	returns (bool)
    {
	if (store.clusterContract[clusterAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    /* Checks whether or not the enrolled user's given ORCID iD is already authenticated in eBlocBroker */
    function isUserOrcIDVerified(address userAddress) public view
	returns (bool)
    {
	if (bytes(store.userContract[userAddress].orcID).length != 0)
	    return true;
	return false;
    }
    
    /* Checks whether or not the given Ethereum address of the user (userAddress) 
       is already registered in eBlocBroker. 
    */
    function isUserExist(address userAddress) public view
	returns (bool)
    {
	if (store.userContract[userAddress].blockReadFrom != 0)
	    return true;
	return false;
    }
    
    /* Used for tests */
    function getReceiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) isClusterExists() public view
	returns (uint getrReceiveStoragePayment) {
	return store.clusterContract[msg.sender].receivedAmountForStorage[jobOwner][sourceCodeHash];
    }

    /* Used for tests */
    function getClusterReceiptSize(address clusterAddress) public view
	returns (uint32)
    {
	return store.clusterContract[clusterAddress].receiptList.getReceiptListSize();
    }

    /* Used for tests */
    function getClusterReceiptNode(address clusterAddress, uint32 index) public view
	returns (uint256, int32)
    {
	return store.clusterContract[clusterAddress].receiptList.printIndex(index);
    }
}
