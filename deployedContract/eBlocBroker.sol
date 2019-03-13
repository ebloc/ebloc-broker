/*
file:   eBlocBroker.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.5;
interface eBlocBrokerInterface {

    /* Logged when the cluster calls receiptCheck function. Records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address indexed clusterAddress,
		     string jobKey,
		     uint index,
		     address recipient,
		     uint received,
		     uint returned,
		     uint endTime,
		     string resultIpfsHash,
		     uint8 storageID,
		     uint dataTransferIn,
		     uint dataTransferOut
		     );

    /* Records the updated jobs' information under setJobStatus() method call */
    event LogSetJob(address indexed clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint startTime
		    );

    /* Records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint indexed index,
		 uint8 storageID,
		 //string desc,
		 string sourceCodeHash,
		 uint32 gasDataTransferIn,
		 uint32 gasDataTransferOut,
		 uint8 cacheType,
		 uint gasStorageHour
		 );

    /* Eecords the registered clusters' registered information under registerCluster() method call.  (fID stands for federationCloudId) */
    event LogCluster(address indexed clusterAddress,
		     uint32 coreNumber,
		     string clusterEmail,
		     string fID,
		     string miniLockID,
		     uint priceCoreMin,
		     uint priceDataTransfer,
		     uint priceStorage,
		     uint priceCache,
		     string ipfsAddress,
		     string whisperPublicKey
		     );

    /* Records the refunded jobs' information under refund() method call */
    event LogRefund(address indexed clusterAddress,
			  string jobKey,
			  uint32 index
			  );

    /* Records the registered users' registered information under registerUser method call.*/
    event LogUser(address userAddress,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string githubUserName,
		  string whisperPublicKey
		  );

    event LogJobDescription(address indexed clusterAddress,
			    string jobKey,
			    string jobDesc
			    );

    event LogStoragePayment(address indexed clusterAddress, uint received);
}


/* Contract Address: 0x */
/// @title eBlocBroker is a blockchain based autonomous computational resource
///        broker.
contract eBlocBroker is eBlocBrokerInterface {

    Lib.Storage s;

    using Lib for Lib.intervalNode;
    using Lib for Lib.clusterData;
    using Lib for Lib.userData;
    using Lib for Lib.status;
    using Lib for Lib.Storage;
    using Lib for Lib.jobStateCodes;

    /* Following function is executed at initialization. It sets contract's deployed
       block number and the owner of the contract.
    */
    constructor() public //constructor() public
    {
	s.deployedBlockNumber = block.number;
	s.owner = msg.sender; /* msg.sender is owner of the smart contract */
    }

    modifier isClusterExists() {
	require(s.clusterContract[msg.sender].blockReadFrom != 0);
	_ ;
    }

    modifier isBehindBlockTimeStamp(uint time) {
	require(time <= block.timestamp);
	_ ;
    }

    modifier deregisterClusterCheck() {
	require(s.clusterContract[msg.sender].blockReadFrom != 0 &&
		s.clusterContract[msg.sender].isRunning);
	_ ;
    }

    modifier checkStateID(uint8 stateID) {
	require(stateID > 2 && stateID <= 15); /*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call */
	_ ;
    }

    modifier isOwner(address addr) {
	require(addr == s.owner);
	_ ;
    }

    modifier isOrcIDverified(address userAddress) {
	require(bytes(s.userContract[userAddress].orcID).length == 0);
	_ ;
    }

    modifier isClusterRegistered() {
	require(s.clusterContract[msg.sender].blockReadFrom == 0);
	_ ;
    }

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
	Lib.status storage job = s.clusterContract[clusterAddress].jobStatus[jobKey][index];

	if (msg.sender != job.jobOwner ||
	    job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED))
	    revert();

	if (job.status == uint8(Lib.jobStateCodes.PENDING) || /* If job have not been started running*/
	   (job.status == uint8(Lib.jobStateCodes.RUNNING) && (block.timestamp - job.startTime) > job.gasCoreMin * 60 + 3600)) /* Job status remain running after one hour that job should have completed */
	    {
		msg.sender.transfer(job.received);
		job.status = uint8(Lib.jobStateCodes.REFUNDED); /* Prevents double spending */
		emit LogRefund(clusterAddress, jobKey, index); /* scancel log */
		return true;
	    }
	else if (job.status == uint8(Lib.jobStateCodes.RUNNING)){
	    emit LogRefund(clusterAddress, jobKey, index); /* scancel log */
	    return true;
	}
	else
	    revert();
    }

    function authenticateOrcID(address userAddress, string memory orcID) isOwner(msg.sender) isOrcIDverified(userAddress) public
	returns (bool success)
    {
	s.userContract[userAddress].orcID = orcID;
	return true;
    }

    /* Following function is a general-purpose mechanism for performing payment withdrawal
       by the cluster provider and paying of unused core usage cost back to the client
    */
    function receiptCheck(string memory jobKey,
			  uint32 index,
			  uint32 jobRunTimeMin,
			  string memory resultIpfsHash,
			  uint8 storageID,
			  uint endTime,
			  uint dataTransferIn,
			  uint dataTransferSum) public
    {
	require(endTime <= block.timestamp);
	/* If "msg.sender" is not mapped on 'clusterContract' array  or its "jobKey" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes
	*/
	Lib.status storage job = s.clusterContract[msg.sender].jobStatus[jobKey][index];
	Lib.clusterInfo memory info = s.clusterContract[msg.sender].info[job.clusterUpdatedBlockNumber];

	require(jobRunTimeMin   <= job.gasCoreMin);      // Cluster cannot request more time of the job that is already requested
	require(dataTransferSum <= job.dataTransferSum); // Cluster cannot request more job's given dataTransferSum amount

	uint amountToGain = 0;
	if (job.dataTransferIn != 0) {
	    require(dataTransferIn <= job.dataTransferIn); // Cluster cannot request more dataTransferIn that is already requested
	    amountToGain += info.priceCache * dataTransferIn; //cacheCost
	}

	amountToGain +=
	    info.priceCoreMin * job.core * jobRunTimeMin + // computationalCost
	    info.priceDataTransfer * (dataTransferSum);    // dataTransferCost

	if (amountToGain > job.received ||
	    job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED))
	    revert();

	if (!s.clusterContract[msg.sender].receiptList.receiptCheck(job, endTime, info.availableCoreNum)) {
	    job.status = uint8(Lib.jobStateCodes.REFUNDED); /* Important to check already refunded job or not */
	    job.jobOwner.transfer(job.received); /* Pay back newOwned(job.received) to the client, full refund */

	    emit LogReceipt(msg.sender, jobKey, index, job.jobOwner, 0, job.received, block.timestamp,
				resultIpfsHash, storageID, dataTransferIn, dataTransferSum);
	    return;// false;
	}
	job.status = uint8(Lib.jobStateCodes.COMPLETED); /* Prevents double spending */
	s.clusterContract[msg.sender].receivedAmount += amountToGain;

	msg.sender.transfer(amountToGain); /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(job.received - amountToGain); /* Unused core and bandwidth is refundedn back to the client */

	emit LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (job.received - amountToGain), block.timestamp, resultIpfsHash, storageID, dataTransferIn, dataTransferSum);
	return; // true;
    }

    function receiveStoragePayment(address jobOwner, string memory sourceCodeHash) isClusterExists() public
	returns (bool success) {
	Lib.clusterData storage cluster = s.clusterContract[msg.sender];

	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum < block.number) {
	    msg.sender.transfer(cluster.receivedAmountForStorage[jobOwner][sourceCodeHash]); //storagePayment
	    emit LogStoragePayment(msg.sender, cluster.receivedAmountForStorage[jobOwner][sourceCodeHash]);
	    cluster.receivedAmountForStorage[jobOwner][sourceCodeHash] = 0;
	    return true;
	}
	return false;
    }

    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates userData */
    function registerUser(string memory userEmail,
			  string memory fID,
			  string memory miniLockID,
			  string memory ipfsAddress,
			  string memory githubUserName,
			  string memory whisperPublicKey) public
	returns (bool success)
    {
	s.userContract[msg.sender].blockReadFrom = block.number;
	//s.userContract[msg.sender].orcID = orcID; //delete
	emit LogUser(msg.sender, userEmail, fID, miniLockID, ipfsAddress, githubUserName, whisperPublicKey);
	return true;
    }

    /* Registers a provider's (msg.sender's) cluster to eBlocBroker */
    function registerCluster(string memory clusterEmail,
			     string memory fID,
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

	Lib.clusterData storage cluster = s.clusterContract[msg.sender];

	require(!cluster.isRunning);
	cluster.info[block.number] = Lib.clusterInfo({
                	availableCoreNum:   availableCoreNum,
                        priceCoreMin:       priceCoreMin,
                        priceDataTransfer:  priceDataTransfer,
                        priceStorage:       priceStorage,
                        priceCache:         priceCache
			});
	s.clusterUpdatedBlockNumber[msg.sender].push(block.number);

	if (cluster.blockReadFrom != 0 && !cluster.isRunning) {
	    s.clusterAddresses[cluster.clusterAddressesID] = msg.sender;
	    cluster.blockReadFrom = block.number;
	    cluster.isRunning = true;
	} else {
	    cluster.clusterAddressesID = uint32(s.clusterAddresses.length);
	    cluster.constructCluster();
	    s.clusterAddresses.push(msg.sender); // In order to obtain the list of clusters
	}

	emit LogCluster(msg.sender, availableCoreNum, clusterEmail, fID, miniLockID,
			    priceCoreMin, priceDataTransfer, priceStorage, priceCache,
			    ipfsAddress, whisperPublicKey);

	return true;
    }

    /* Locks the access to the Cluster. Only cluster owner could stop it */
    function deregisterCluster() public
	returns (bool success)
    {
	delete s.clusterAddresses[s.clusterContract[msg.sender].clusterAddressesID];
	s.clusterContract[msg.sender].isRunning = false; /* Cluster wont accept any more jobs */
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateCluster(string memory clusterEmail,
			   string memory fID,
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
	Lib.clusterData storage cluster = s.clusterContract[msg.sender];
	if (cluster.blockReadFrom == 0 || cluster.info[block.number].availableCoreNum != 0)
	    revert();

	cluster.info[block.number] = Lib.clusterInfo({
                	availableCoreNum:   availableCoreNum,
                        priceCoreMin:       priceCoreMin,
                        priceDataTransfer:  priceDataTransfer,
                        priceStorage:       priceStorage,
                        priceCache:         priceCache
			});
	s.clusterUpdatedBlockNumber[msg.sender].push(block.number);
	cluster.blockReadFrom = block.number;

	emit LogCluster(msg.sender, availableCoreNum, clusterEmail, fID, miniLockID,
			    priceCoreMin, priceDataTransfer, priceStorage, priceCache,
			    ipfsAddress, whisperPublicKey);
	return true;
    }

    /* Performs a job submission to eBlocBroker by a client */
    function submitJob(address payable clusterAddress,
		       string memory jobKey,
		       uint32 core,
		       uint32 gasCoreMin,
		       uint32 dataTransferIn,
		       uint32 dataTransferOut,
		       uint8 storageID,
		       string memory sourceCodeHash,
		       uint8 cacheType,
		       uint gasStorageHour) public payable
    {
	uint[] storage clusterInfo = s.clusterUpdatedBlockNumber[clusterAddress];
 	Lib.clusterData storage cluster = s.clusterContract[clusterAddress];
	Lib.clusterInfo storage info = cluster.info[clusterInfo[clusterInfo.length-1]];

	if (cluster.jobSt[sourceCodeHash].receivedBlocNumber + cluster.jobSt[sourceCodeHash].gasStorageBlockNum > block.number){
	    if (cluster.receivedAmountForStorage[msg.sender][sourceCodeHash] != 0)
		dataTransferIn = 0;
	}
	else
	    dataTransferOut = dataTransferIn + dataTransferOut;

	if (core == 0 || msg.value == 0 || !cluster.isRunning || storageID > 4 || gasCoreMin == 0 ||
	    gasCoreMin > 1440 || // gasCoreMin is maximum 1 day
	    msg.value < info.priceCoreMin * core * gasCoreMin +                // computationalCost
	                info.priceDataTransfer * (dataTransferOut) +           // dataTransferCost
	                info.priceStorage * dataTransferIn * gasStorageHour +  // storageCost
	              	info.priceCache * dataTransferIn                       // cacheCost
	    ||
	    bytes(jobKey).length > 255 || // Max length is 255 for the filename
	    (bytes(sourceCodeHash).length != 32 && bytes(sourceCodeHash).length != 0) ||
	    !isUserExist(msg.sender) ||
	    bytes(s.userContract[msg.sender].orcID).length == 0 ||
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
		emit LogStoragePayment(clusterAddress, cluster.receivedAmountForStorage[msg.sender][sourceCodeHash]);
	    }

	    cluster.jobSt[sourceCodeHash].receivedBlocNumber = block.number;
	    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
	    cluster.jobSt[sourceCodeHash].gasStorageBlockNum = gasStorageHour * 240;
	    cluster.receivedAmountForStorage[msg.sender][sourceCodeHash] = info.priceStorage * dataTransferIn * gasStorageHour;
	}

	emit LogJob(clusterAddress, jobKey, cluster.jobStatus[jobKey].length - 1, storageID, sourceCodeHash,
			dataTransferIn, dataTransferOut, cacheType, gasStorageHour);
	return;
    }

    function updateJobReceivedBlocNumber(string memory sourceCodeHash) public
	returns (bool success)
    {
	Lib.clusterData storage cluster = s.clusterContract[msg.sender]; //Only cluster can update receied job only to itself
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
	if (msg.sender == s.clusterContract[clusterAddress].jobStatus[jobKey][0].jobOwner)
	    emit LogJobDescription(clusterAddress, jobKey, jobDesc);
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(string memory jobKey, uint32 index, uint8 stateID, uint startTime)
	isBehindBlockTimeStamp(startTime)
	checkStateID(stateID) public
	returns (bool success)
    {
	Lib.status storage job = s.clusterContract[msg.sender].jobStatus[jobKey][index]; /* Used as a pointer to a storage */
	if (job.status == uint8(Lib.jobStateCodes.COMPLETED) ||
	    job.status == uint8(Lib.jobStateCodes.REFUNDED)  ||
	    job.status == uint8(Lib.jobStateCodes.RUNNING)) /* Cluster can sets job's status as RUNNING and its startTime only one time */
	    revert();
	job.status = stateID;
	if (stateID == uint8(Lib.jobStateCodes.RUNNING))
	    job.startTime = startTime;

	emit LogSetJob(msg.sender, jobKey, index, startTime);
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
	if (s.userContract[userAddress].blockReadFrom != 0)
	    return (s.userContract[userAddress].blockReadFrom, s.userContract[userAddress].orcID);
    }

    /* Returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses */
    function getClusterInfo(address clusterAddress) public view
	returns(uint, uint, uint, uint, uint, uint)
    {
	if (s.clusterContract[clusterAddress].blockReadFrom != 0) {
	    uint[] memory clusterInfo = s.clusterUpdatedBlockNumber[clusterAddress];

	    return (s.clusterContract[clusterAddress].blockReadFrom,
		    s.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].availableCoreNum,
		    s.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceCoreMin,
		    s.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceDataTransfer,
		    s.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceStorage,
		    s.clusterContract[clusterAddress].info[clusterInfo[clusterInfo.length-1]].priceCache);
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
	uint arrayLength = s.clusterContract[clusterAddress].jobStatus[jobKey].length;
        if (arrayLength == 0)
	    return (0, 0, 0, 0, 0, address(0x0));

        if (arrayLength <= index)
	    return (0, 0, 0, 0, 0, address(0x0));

	Lib.status memory job = s.clusterContract[clusterAddress].jobStatus[jobKey][index];
	//Lib.clusterInfo memory clusterInfo =  s.clusterContract[clusterAddress].info[job.clusterUpdatedBlockNumber];

	return (job.status, job.core, job.startTime, job.received, job.gasCoreMin, job.jobOwner);
    }

    function getClusterPricesForJob(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.status memory job = s.clusterContract[clusterAddress].jobStatus[jobKey][index];
	Lib.clusterInfo memory clusterInfo = s.clusterContract[clusterAddress].info[job.clusterUpdatedBlockNumber];

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
	return s.clusterUpdatedBlockNumber[clusterAddress];
    }

    /* Returns the contract's deployed block number */
    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return s.deployedBlockNumber;
    }

    /* Returns the owner of the contract */
    function getOwner() public view
	returns (address)
    {
	return s.owner;
    }

    function getJobSize(address clusterAddress, string memory jobKey) public view
	returns (uint)

    {
	if (s.clusterContract[msg.sender].blockReadFrom == 0)
	    revert();
	return s.clusterContract[clusterAddress].jobStatus[jobKey].length;
    }

    /* Returns cluster provider's earned money amount in Wei.
       It takes a cluster's Ethereum address (clusterAddress) as parameter.
    */
    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint)
    {
	return s.clusterContract[clusterAddress].receivedAmount;
    }

    /* Returns a list of registered cluster Ethereum addresses */
    function getClusterAddresses() public view
	returns (address[] memory)
    {
	return s.clusterAddresses;
    }

    function getJobStorageTime(address clusterAddress, string memory sourceCodeHash) public view
	returns(uint, uint)
    {
	Lib.clusterData storage cluster = s.clusterContract[clusterAddress];
	return (cluster.jobSt[sourceCodeHash].receivedBlocNumber,
		cluster.jobSt[sourceCodeHash].gasStorageBlockNum / 240);
    }

    /* Checks whether or not the given Ethereum address of the provider (clusterAddress)
       is already registered in eBlocBroker.
    */
    function isClusterExist(address clusterAddress) public view
	returns (bool)
    {
	if (s.clusterContract[clusterAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    /* Checks whether or not the enrolled user's given ORCID iD is already authenticated in eBlocBroker */
    function isUserOrcIDVerified(address userAddress) public view
	returns (bool)
    {
	if (bytes(s.userContract[userAddress].orcID).length != 0)
	    return true;
	return false;
    }

    /* Checks whether or not the given Ethereum address of the user (userAddress)
       is already registered in eBlocBroker.
    */
    function isUserExist(address userAddress) public view
	returns (bool)
    {
	if (s.userContract[userAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    /* Used for tests */
    function getReceiveStoragePayment(address jobOwner, string memory sourceCodeHash) isClusterExists() public view
	returns (uint getrReceiveStoragePayment) {
	return s.clusterContract[msg.sender].receivedAmountForStorage[jobOwner][sourceCodeHash];
    }

    /* Used for tests */
    function getClusterReceiptSize(address clusterAddress) public view
	returns (uint32)
    {
	return s.clusterContract[clusterAddress].receiptList.getReceiptListSize();
    }

    /* Used for tests */
    function getClusterReceiptNode(address clusterAddress, uint32 index) public view
	returns (uint256, int32)
    {
	return s.clusterContract[clusterAddress].receiptList.printIndex(index);
    }
}


library Lib {

    enum jobStateCodes {
	NULL,      /* 0 */
	COMPLETED, /* 1 Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,  /* 2 Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,   /* 3 */
	RUNNING    /* 4 */
    }

    struct Storage {
	/* Uninitialized uint variable that will be set with the block number that will be obtained when contract is constructed */
	uint      deployedBlockNumber;
	address   owner;
	address[] clusterAddresses; /* A dynamically-sized array of `address` structs */
	mapping(address => uint[]) clusterUpdatedBlockNumber;
	mapping(address => Lib.clusterData) clusterContract;
	mapping(address => Lib.userData) userContract;
    }

    struct jobStorageTime {
	uint receivedBlocNumber;
	uint gasStorageBlockNum;
    }

    /* Submitted Job's information */
    struct status {
	/* Variable assigned by the cluster */
	uint8        status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint      startTime; /* Submitted job's starting universal time on the server side */

	/* Variables assigned by the client */
	uint     gasCoreMin; /* Time to run job in minutes. ex: minute + hour * 60 + day * 1440; */
	uint dataTransferIn;  /**/
	uint dataTransferSum; /**/
	uint32         core; /* Requested core by the client */

	/* Variables obtained from eBlocBoker */
	uint    received; /* Paid amount (new owned) by the client */
	address payable jobOwner; /* Address of the client (msg.sender) has been stored */
	uint clusterUpdatedBlockNumber; /* When cluster is submitted cluster's most recent block number when its set or updated */
    }

    /* Registered user's information */
    struct userData {
	uint   blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
	string         orcID; /* User's orcID */

	//mapping(address => mapping(string  => bool)) isStoragePaid; /**/
    }

    struct clusterInfo {
	uint32 availableCoreNum; /* Core number of the cluster */
	/* All price varaibles are defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */
	uint   priceCoreMin; /* Cluster's price for core per minute */
	uint   priceDataTransfer;
	uint   priceStorage;
	uint   priceCache;
    }

    /* Registered cluster's information */
    struct clusterData {
	intervalNode receiptList; /* receiptList will be use to check either job's start and end time overlapped or not */

	mapping(string => status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	mapping(uint => clusterInfo) info;
	mapping(string  => jobStorageTime) jobSt; /*Stored information related to job's storage time*/
	mapping(address => mapping(string  => uint)) receivedAmountForStorage; /**/

	bool            isRunning; /* Flag that checks is Cluster running or not */
	uint32 clusterAddressesID; /* Index of cluster's ethereum address is stored in clusterAddresses */
	uint       receivedAmount; /* Cluster's received wei price */
	uint        blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
    }

    struct interval {
	uint endpoint;
	int32   core; /* Job's requested core number */
	uint32  next; /* Points to next the node */
    }

    struct intervalNode {
	interval[] list; /* A dynamically-sized array of `interval` structs */
	uint32 tail; /* Tail of the linked list */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }

    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(clusterData storage self) public
    {
	self.isRunning      = true;
	self.receivedAmount = 0;
	self.blockReadFrom  = block.number;

	intervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
	selfReceiptList.tail             = 0;
	selfReceiptList.deletedItemNum   = 0;
    }

    function receiptCheck(intervalNode storage self, status storage job, uint endTime, uint availableCoreNum) public
	returns (bool success)
    {
	bool   flag = false;
	uint32 addr = self.tail;
	uint32 addrTemp;
	int32  carriedSum;

	interval storage prevNode     = self.list[0];
	interval storage currentNode  = self.list[0];
	interval storage prevNodeTemp = self.list[0];

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (endTime < self.list[addr].endpoint) {
	    flag        = true;
	    prevNode    = self.list[addr];
	    currentNode = self.list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do {
		if (endTime > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to push the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next];
	    } while (true);
	}

	self.list.push(interval({endpoint: endTime, core: int32(job.core), next: addr})); /* Inserted while keeping sorted order */
	carriedSum = int32(job.core); /* Carried sum variable is assigned with job's given core number */

	if (!flag) {
	    addrTemp      = addr;
	    prevNode      = self.list[self.tail = uint32(self.list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(self.list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = self.list[prevNode.next]; /* Current node points index before insert operation is done */

	do { /* Inside while loop carriedSum is updated */
	    if (job.startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		self.list.push(interval( {endpoint: job.startTime, core: -1 * int32(job.core), next: prevNode.next}));
		prevNode.next = uint32(self.list.length - 1);
		return true;
	    }
	    carriedSum += currentNode.core;

	    /* If enters into if statement it means revert() is catch and all previous operations are reverted back */
	    if (carriedSum > int32(availableCoreNum)) {
		delete self.list[self.list.length-1];
		if (!flag)
		    self.tail = addrTemp;
		else
		    prevNodeTemp.next = addrTemp;

		self.deletedItemNum += 1;
		return false;
	    }
	    prevNode    = currentNode;
	    currentNode = self.list[currentNode.next];
	} while (true);

	// +-----------------------------+
	// | End: receiptCheck Algorithm |
	// +-----------------------------+
    }

    /* Used for tests */
    function getReceiptListSize(intervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length-self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(intervalNode storage self, uint32 index) public view
	returns (uint256, int32)
    {
	uint32 myIndex = self.tail;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;

	return (self.list[myIndex].endpoint, self.list[myIndex].core);
    }
}
