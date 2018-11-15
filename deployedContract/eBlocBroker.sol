/*
file:   Lib.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.4.24;

library Lib {
    /* Submitted Job's information */
    struct status {
	/* Variable assigned by the cluster */
	uint8          status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint        startTime; /* Submitted job's starting universal time on the server side */	
	/* Variables assigned by the client */	
	uint         received; /* Paid amount by the client */
	uint     priceCoreMin; /* Cluster's price for core/minute */
	uint       gasCoreMin; /* Time to run job in minutes. ex: minute + hour * 60 + day * 1440; */
	uint priceBandwidthMB;
	uint32           core; /* Requested core by the client */
	address      jobOwner; /* Address of the client (msg.sender) has been stored */
    }

    /* Registered user's information */
    struct userData {
	uint     blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
	string   orcID; /* User's orcID */
    }

    /* Registered cluster's information */
    struct clusterData {
	bool            isRunning; /* Flag that checks is Cluster running or not */
	uint32 clusterAddressesID; /* Cluster's ethereum address is stored */
	uint         priceCoreMin; /* Should be defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */
	uint     priceBandwidthMB; /* Should be defined in wei. */
	uint       receivedAmount; /* Cluster's received wei price */
	uint        blockReadFrom; /* Blockn number when cluster is registered in order the watch cluster's event activity */

	mapping(string => status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	intervalNode    receiptList; /* receiptList will be use to check either job's start and end time overlapped or not */
    }

    struct interval {
	uint   endpoint;
	int32  core; /* Job's requested core number */
	uint32 next; /* Points to next the node */
    }

    struct intervalNode {
	interval[] list; /* A dynamically-sized array of `interval` structs */
	uint32 tail; /* Tail of the linked list */
	uint32 coreNumber; /* Core number of the cluster */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }

    /* Invoked, when cluster calls updateCluster() function */
    function update(clusterData storage self, uint priceCoreMin, uint priceBandwidthMB, uint32 coreNumber) public
    {
	self.priceCoreMin           = priceCoreMin;
	self.priceBandwidthMB       = priceBandwidthMB;
	self.receiptList.coreNumber = coreNumber;
	self.blockReadFrom          = block.number;
    }    

    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(clusterData storage self, uint32 memLen, uint priceCoreMin, uint priceBandwidthMB, uint32 coreNumber) public
    {
	self.isRunning          = true;
	self.receivedAmount     = 0;
	self.clusterAddressesID = memLen;
	self.priceCoreMin    = priceCoreMin;
	self.priceBandwidthMB  = priceBandwidthMB;
	self.blockReadFrom      = block.number;

	intervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted */
	selfReceiptList.tail           = 0;
	selfReceiptList.coreNumber     = coreNumber;
	selfReceiptList.deletedItemNum = 0;
    }

    function receiptCheck(intervalNode storage self, uint startTime, uint endTime, int32 coreNum) public
	returns (bool success)
    {
	bool     flag = false;
	uint32   addr = self.tail;
	uint32   addrTemp;
	int32    carriedSum;
	interval storage prevNode;
	interval storage currentNode;
	interval storage prevNodeTemp;

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (endTime < self.list[addr].endpoint) {
	    flag         = true;
	    prevNode     = self.list[addr];
	    currentNode  = self.list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { /* Inside while loop carriedSum is updated */
		//carriedSum += prevNode.core;
		if (endTime > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to push the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next];
	    } while (true);
	}

	self.list.push(interval({endpoint: endTime, core: coreNum, next: addr})); /* Inserted while keeping sorted order */
	carriedSum = coreNum; /* Carried sum variable is assigned with job's given core number */
	
	if (!flag) {
	    addrTemp      = addr;	    
	    prevNode      = self.list[self.tail = uint32(self.list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(self.list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = self.list[prevNode.next]; /* Current node points index before insert operation is done */

	do {
	    if (startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		self.list.push(interval( {endpoint: startTime, core: -1*coreNum, next: prevNode.next}));
		prevNode.next = uint32(self.list.length - 1);
		return true;
	    }
	    carriedSum += currentNode.core;

	    /* If enters into if statement it means revert() is catch and all previous operations are reverted back */
	    if (carriedSum > int32(self.coreNumber)) {
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

    /* Could be commented out, used for test */
    function getReceiptListSize(intervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length-self.deletedItemNum);
    }

    /* Could be commented out, used for test */
    function printIndex(intervalNode storage self, uint32 index) public view
	returns (uint256, int32)
    {
	uint32 myIndex = self.tail;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;

	return (self.list[myIndex].endpoint, self.list[myIndex].core);
    }
}

contract eBlocBroker {

    uint    deployedBlockNumber; /* The block number that was obtained when contract is deployed */
    address owner;

    enum jobStateCodes {
	NULL,      /* 0 */
	COMPLETED, /* 1 Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,  /* 2 Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,   /* 3 */
	RUNNING    /* 4 */
    }

    using Lib for Lib.intervalNode;
    using Lib for Lib.clusterData;
    using Lib for Lib.userData;
    using Lib for Lib.status;

    address[] clusterAddresses; /* A dynamically-sized array of `address` structs */
    address[] userAddresses;    /* A dynamically-sized array of `address` structs */

    mapping(address => Lib.clusterData) clusterContract;
    mapping(address => Lib.userData)    userContract;
    mapping(string  => uint32)          verifyOrcID;

    modifier check_gasCoreMin_storageID(uint32 gasCoreMin, uint8 storageID) {
	/* gasCoreMin is maximum 1 day */
	require(storageID < 5 && !(gasCoreMin == 0 || gasCoreMin > 1440)); 
	_ ;
    }

    modifier deregisterClusterCheck() {
	require(clusterContract[msg.sender].blockReadFrom != 0 &&
		clusterContract[msg.sender].isRunning);
	_ ;
    }

    modifier isBehindBlockTimeStamp(uint time) {
	require(time <= block.timestamp);
	_ ;
    }
    /*
    modifier isZero(uint32 input) {
	require(input != 0);
	_ ;
    }
    */
    modifier checkStateID(uint8 stateID) {
	require(stateID <= 15 && stateID > 2); /*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call.*/
	_ ;
    }

    modifier isOwner(address addr) {
	require(addr == owner);
	_ ;
    }

    /* Following function is executed at initialization. It sets contract's deployed 
       block number and the owner of the contract. 
    */
    constructor() public //constructor() public
    {
	deployedBlockNumber = block.number;
	owner = msg.sender; /* Owner of the smart contract */
    }

    /* Refund funds the complete amount to client if requested job is still in the pending state or
       is not completed one hour after its required time.
       If the job is in the running state, it triggers LogCancelRefund event on the blockchain, 
       which will be caught by the cluster in order to cancel the job. 
    */
    function cancelRefund(address clusterAddress, string memory jobKey, uint32 index) public
	returns (bool)
    {
	/* If 'clusterAddress' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = clusterContract[clusterAddress].jobStatus[jobKey][index];

	if (msg.sender != job.jobOwner || job.status == uint8(jobStateCodes.COMPLETED) || job.status == uint8(jobStateCodes.REFUNDED))
	    revert();

	if (job.status == uint8(jobStateCodes.PENDING) || /* If job have not been started running*/
	    (job.status == uint8(jobStateCodes.RUNNING) && (block.timestamp - job.startTime) > job.gasCoreMin * 60 + 3600)) /* Job status remain running after one hour that job should have completed */
	    {
		msg.sender.transfer(job.received);
		job.status = uint8(jobStateCodes.REFUNDED); /* Prevents double spending */
		emit LogCancelRefund(clusterAddress, jobKey, index); /* scancel log */
		return true;
	    }
	else if (job.status == uint8(jobStateCodes.RUNNING)){
	    emit LogCancelRefund(clusterAddress, jobKey, index); /* scancel log */
	    return true;
	}
	else
	    revert();
    }

    /* Following function is a general-purpose mechanism for performing payment withdrawal
       by the cluster provider and paying of unused core usage cost back to the client
    */
    function receiptCheck(string memory jobKey, uint32 index, uint32 jobRunTimeMin, string memory resultIpfsHash,
			  uint8 storageID, uint endTime, uint usedBandwidthMB)
	isBehindBlockTimeStamp(endTime) public
	returns (bool success) /* Payback to client and server */
    {
	/* If 'msg.sender' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = clusterContract[msg.sender].jobStatus[jobKey][index];

	//uint netOwned     = job.received;
	uint amountToGain = job.priceCoreMin * job.core * jobRunTimeMin + job.priceBandwidthMB * usedBandwidthMB;

	if (amountToGain > job.received ||
	    job.status == uint8(jobStateCodes.COMPLETED) ||
	    job.status == uint8(jobStateCodes.REFUNDED))
	    revert();

	if (!clusterContract[msg.sender].receiptList.receiptCheck(job.startTime, endTime, int32(job.core))) {
	    job.status = uint8(jobStateCodes.REFUNDED); /* Important to check already refunded job or not */
	    job.jobOwner.transfer(job.received); /* Pay back newOwned(job.received) to the client, full refund */

	    emit LogReceipt(msg.sender, jobKey, index, job.jobOwner, 0, job.received, block.timestamp,
				resultIpfsHash, storageID, usedBandwidthMB);
	    return false;
	}
	job.status = uint8(jobStateCodes.COMPLETED); /* Prevents double spending */
	clusterContract[msg.sender].receivedAmount += amountToGain;
	
	msg.sender.transfer(amountToGain); /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(job.received - amountToGain); /* Unused core and bandwidth is refundedn back to the client */

	emit LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (job.received - amountToGain),
			    block.timestamp, resultIpfsHash, storageID, usedBandwidthMB);
	return true;
    }
    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates userData. */
    function registerUser(string memory userEmail, string memory fID, string memory miniLockID,
			  string memory ipfsAddress, string memory orcID,
			  string memory githubUserName, string memory whisperPublicKey) public
	returns (bool success)
    {
	userContract[msg.sender].blockReadFrom = block.number;
	userContract[msg.sender].orcID = orcID;
	emit LogUser(msg.sender, userEmail, fID, miniLockID, ipfsAddress, orcID, githubUserName, whisperPublicKey);
	return true;
    }

    function authenticateOrcID(string memory orcID) isOwner(msg.sender) public
	returns (bool success)
    {
	verifyOrcID[orcID] = 1;
	return true;
    }

    /* Registers a provider's (msg.sender's) cluster to eBlocBroker. */
    function registerCluster(uint32 coreNumber, string memory clusterEmail, string memory fID,
			     string memory miniLockID, uint priceCoreMin, uint priceBandwidthMB,
			     string memory ipfsAddress, string memory whisperPublicKey) public
	returns (bool success)
    {
	if (coreNumber == 0 || priceCoreMin == 0 || priceBandwidthMB == 0)
	    revert();
	
	Lib.clusterData storage cluster = clusterContract[msg.sender];
	if (cluster.blockReadFrom != 0 && cluster.isRunning)
	    revert();

	if (cluster.blockReadFrom != 0 && !cluster.isRunning) {
	    clusterAddresses[cluster.clusterAddressesID] = msg.sender;
	    cluster.update(priceCoreMin, priceBandwidthMB, coreNumber);
	    cluster.isRunning = true;
	} else {
	    cluster.constructCluster(uint32(clusterAddresses.length), priceCoreMin, priceBandwidthMB, coreNumber);
	    clusterAddresses.push(msg.sender); /* In order to obtain list of clusters */
	}

	emit LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID,
			    priceCoreMin, priceBandwidthMB, ipfsAddress, whisperPublicKey);
	return true;
    }

    /* Locks the access to the Cluster. Only cluster owner could stop it */
    function deregisterCluster() public returns (bool success)
    {
	delete clusterAddresses[clusterContract[msg.sender].clusterAddressesID];
	clusterContract[msg.sender].isRunning = false; /* Cluster wont accept any more jobs */
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateCluster(uint32 coreNumber, string memory clusterEmail, string memory fID,
			   string memory miniLockID, uint priceCoreMin, uint priceBandwidthMB,
			   string memory ipfsAddress, string memory whisperPublicKey)
	public returns (bool success)
    {
	Lib.clusterData storage cluster = clusterContract[msg.sender];
	if (cluster.blockReadFrom == 0)
	    revert();

	clusterContract[msg.sender].update(priceCoreMin, priceBandwidthMB, coreNumber);

	emit LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID,
			    priceCoreMin, priceBandwidthMB, ipfsAddress, whisperPublicKey);
	return true;
    }

    /* Performs a job submission to eBlocBroker by a client. */
    function submitJob(address clusterAddress, string memory jobKey, uint32 core,
		       string memory jobDesc, uint32 gasCoreMin, uint32 gasBandwidthMB,
		       uint8 storageID, string memory folderHash)
	check_gasCoreMin_storageID(gasCoreMin, storageID)  /*isZero(core)*/  public payable
	returns (bool success)
    {	
 	Lib.clusterData storage cluster = clusterContract[clusterAddress];

	if (core == 0 || msg.value == 0                                       ||
	    !cluster.isRunning                                                ||
	    msg.value < cluster.priceCoreMin * gasCoreMin * core              ||
	    bytes(jobKey).length > 255                                        || // Max length is 255 for the filename 
	    (bytes(folderHash).length != 32 && bytes(folderHash).length != 0) ||
	    !isUserExist(msg.sender)                                          ||
	    verifyOrcID[userContract[msg.sender].orcID] == 0                  ||	    
	    core > cluster.receiptList.coreNumber)
	    revert();

	Lib.status [] storage jobStatus = cluster.jobStatus[jobKey];

	jobStatus.push(Lib.status({
      		        status:         uint8(jobStateCodes.PENDING),
			core:           core,                       /* Requested core value */
			gasCoreMin:     gasCoreMin,                 //
			jobOwner:       msg.sender,
			received:       msg.value,
			priceCoreMin:   cluster.priceCoreMin,       //
			priceBandwidthMB: cluster.priceBandwidthMB, //
			startTime:      0
			}
		));	
	emit LogJob(clusterAddress, jobKey, jobStatus.length - 1, storageID, jobDesc, folderHash);
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm. */
    function setJobStatus(string memory jobKey, uint32 index, uint8 stateID, uint startTime) isBehindBlockTimeStamp(startTime) public
	checkStateID(stateID) returns (bool success)
    {
	Lib.status storage job = clusterContract[msg.sender].jobStatus[jobKey][index]; /* Used as a pointer to a storage */
	if (job.status == uint8(jobStateCodes.COMPLETED) ||
	    job.status == uint8(jobStateCodes.REFUNDED)  ||
	    job.status == uint8(jobStateCodes.RUNNING)) /* Cluster can sets job's status as RUNNING and its startTime only one time */
	    revert();
	job.status = stateID;
	if (stateID == uint8(jobStateCodes.RUNNING))
	    job.startTime = startTime;

	emit LogSetJob(msg.sender, jobKey, index, startTime);
	return true;
    }

    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* Returns a list of registered cluster Ethereum addresses. */
    function getClusterAddresses() public view
	returns (address[] memory)
    {
	return clusterAddresses;
    }

    /* Checks whether or not the given ORCID iD is already authenticated in eBlocBroker. */
    function isOrcIDVerified(string memory orcID) public view
	returns (uint32)
    {
	return verifyOrcID[orcID];
    }

    /* Returns the enrolled user's
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event.
       It takes Ethereum address of the user (userAddress), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address userAddress) public view
	returns(uint, string memory )
    {
	if (userContract[userAddress].blockReadFrom != 0)
	    return (userContract[userAddress].blockReadFrom, userContract[userAddress].orcID);
    }

    /* Returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses. */
    function getClusterInfo(address clusterAddress) public view
	returns(uint, uint, uint, uint)
    {
	if (clusterContract[clusterAddress].blockReadFrom != 0)
	    return (clusterContract[clusterAddress].blockReadFrom,
		    clusterContract[clusterAddress].receiptList.coreNumber,
		    clusterContract[clusterAddress].priceCoreMin,
		    clusterContract[clusterAddress].priceBandwidthMB);
	else
	    return (0, 0, 0, 0);
    }

    /* Returns cluster provider's earned money amount in Wei.
       It takes a cluster's Ethereum address (clusterAddress) as parameter. 
    */
    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint)
    {
	return clusterContract[clusterAddress].receivedAmount;
    }

    function getJobSize(address clusterAddress, string memory jobKey) public view
	returns (uint)

    {
	if (clusterContract[msg.sender].blockReadFrom == 0)
	    revert();
	return clusterContract[clusterAddress].jobStatus[jobKey].length;
    }

    /* Returns various information about the submitted job such as the hash of output files generated by IPFS,
       UNIX timestamp on job's start time, received Wei value from the client etc. 
    */
    function getJobInfo(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, uint, address)
    {
	uint arrayLength = clusterContract[clusterAddress].jobStatus[jobKey].length;
        if (arrayLength == 0)
	    return (0, 0,  0, 0, 0, 0, address(0x0));
	
        if (arrayLength <= index)
	    return (0, 0,  0, 0, 0, 0, address(0x0));
	
	Lib.status memory job = clusterContract[clusterAddress].jobStatus[jobKey][index];	
	return (job.status, job.core, job.startTime, job.received, job.priceCoreMin, job.gasCoreMin, job.jobOwner);
    }

    /* Returns the contract's deployed block number. */
    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return deployedBlockNumber;
    }

    /* Returns the owner of the contract. */
    function getOwner() public view
	returns (address)
    {
	return owner;
    }

    /* Checks whether or not the given Ethereum address of the provider (clusterAddress) is already registered in eBlocBroker. */
    function isClusterExist(address clusterAddress) public view
	returns (bool)
    {
	if (clusterContract[clusterAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    /* Checks whether or not the given Ethereum address of the provider (userAddress) is already registered in eBlocBroker. */
    function isUserExist(address userAddress) public view
	returns (bool)
    {
	if (userContract[userAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    function getClusterReceiptSize(address clusterAddress) public view
	returns (uint32)
    {
	return clusterContract[clusterAddress].receiptList.getReceiptListSize();
    }

    function getClusterReceiptNode(address clusterAddress, uint32 index) public view
	returns (uint256, int32)
    {
	return clusterContract[clusterAddress].receiptList.printIndex(index);
    }

    /* -----------------------------------------------------EVENTS---------------------------------------------------------*/    
    /* Records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint index,
		 uint8 storageID,
		 string desc,
		 string folderHash
		 );

    /* Records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address clusterAddress,
		     string jobKey,
		     uint index,
		     address recipient,
		     uint received,
		     uint returned,
		     uint endTime,
		     string resultIpfsHash,
		     uint8 storageID,
		     uint usedBandwidthMB
		     );

    /* Eecords the registered clusters' registered information under registerCluster() method call.  (fID stands for federationCloudId) */
    event LogCluster(address clusterAddress,
		     uint32 coreNumber,
		     string clusterEmail,
		     string fID,
		     string miniLockID,
		     uint priceCoreMin,
		     uint priceBandwidthMB,
		     string ipfsAddress,
		     string whisperPublicKey
		     );

    /* Records the registered users' registered information under registerUser method call.*/
    event LogUser(address userAddress,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string orcID,
		  string githubUserName,
		  string whisperPublicKey
		  );

    /* Records the refunded jobs' information under refund() method call. */
    event LogCancelRefund(address indexed clusterAddress,
			  string jobKey,
			  uint32 index
			  );

    /* Records the updated jobs' information under setJobStatus() method call. */
    event LogSetJob(address clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint startTime
		    );
}
