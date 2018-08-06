pragma solidity ^0.4.17; import "./Lib.sol";

// GitHub Commit Hash: 
contract eBlocBroker {

    uint    deployedBlockNumber; /* The block number that was obtained when contract is deployed */
    address owner;

    enum jobStateCodes {
	NULL,      //0
	COMPLETED, //1 /* Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,  //2 /* Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,   //3
	RUNNING    //4
    }

    using Lib for Lib.intervalNode;
    using Lib for Lib.clusterData;
    using Lib for Lib.userData;
    using Lib for Lib.status;

    address[] clusterAddresses; // A dynamically-sized array of `address` structs
    address[] userAddresses;    // A dynamically-sized array of `address` structs

    mapping(address => Lib.clusterData) clusterContract;
    mapping(address => Lib.userData)       userContract;
    mapping(string  => uint32)              verifyOrcid;

    modifier coreMinuteGas_storageID_check(uint32 coreMinuteGas, uint8 storageID) {
	require(storageID < 5 && !(coreMinuteGas == 0 || coreMinuteGas > 1440)); /* coreMinuteGas is maximum 1 day */
	_ ;
    }

    modifier deregisterClusterCheck() {
	require(clusterContract[msg.sender].blockReadFrom != 0 && clusterContract[msg.sender].isRunning);
	_ ;
    }

    modifier isBehindBlockTimeStamp(uint time) {
	require(time <= block.timestamp);
	_ ;
    }

    modifier isZero(uint32 input) {
	require(input != 0);
	_ ;
    }

    modifier stateID_check(uint8 stateID) {
	require(stateID <= 15 && stateID > 2); /*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call.*/
	_ ;
    }

    modifier isOwner(address addr) {
	require(addr == owner);
	_ ;
    }

    // Following function is executed at initialization. It sets contract's deployed block number and the owner of the contract.
    function eBlocBroker() public //constructor() public
    {
	deployedBlockNumber = block.number;
	owner = msg.sender; /* Owner of the smart contract */
    }

    /* cancelRefund() function refunds the complete amount to client if requested job is still in the pending state or
    is not completed one hour after its required time.
    If the job is in the running state, it triggers LogCancelRefund event on the blockchain, which will be caught by the cluster in
    order to cancel the job. */
    function cancelRefund(address clusterAddress, string jobKey, uint32 index) public returns (bool)
    {
	/* If 'clusterAddress' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = clusterContract[clusterAddress].jobStatus[jobKey][index];

	if (msg.sender != job.jobOwner || job.status == uint8(jobStateCodes.COMPLETED) || job.status == uint8(jobStateCodes.REFUNDED))
	    revert();

	if (job.status == uint8(jobStateCodes.PENDING) || /* If job have not been started running*/
	    (job.status == uint8(jobStateCodes.RUNNING) && (block.timestamp - job.startTime) > job.coreMinuteGas * 60 + 3600)) /* Job status remain running after one hour that job should have completed */
	    {
		msg.sender.transfer(job.received);
		job.status = uint8(jobStateCodes.REFUNDED); /* Prevents double spending */
		/*emit*/ LogCancelRefund(clusterAddress, jobKey, index);   /* scancel log */
		return true;
	    }
	else if (job.status == uint8(jobStateCodes.RUNNING)){
	    /*emit*/ LogCancelRefund(clusterAddress, jobKey, index);   /* scancel log */
	    return true;
	}
	else
	    revert();
    }

    /* receiptCheck function is a general-purpose mechanism for performing payment withdrawal
       by the cluster provider and paying of unused core usage cost back to the client
    */
    function receiptCheck(string jobKey, uint32 index, uint32 jobRunTimeMinute, string resultIpfsHash, uint8 storageID, uint endTime)
	isBehindBlockTimeStamp(endTime) public returns (bool success) /* Payback to client and server */
    {
	/* If 'msg.sender' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = clusterContract[msg.sender].jobStatus[jobKey][index];

	uint netOwned     = job.received;
	uint amountToGain = job.coreMinutePrice * job.core * jobRunTimeMinute;

	if((amountToGain > netOwned) || job.status == uint8(jobStateCodes.COMPLETED) || job.status == uint8(jobStateCodes.REFUNDED) )
	    revert();

	if (!clusterContract[msg.sender].receiptList.receiptCheck(job.startTime, endTime, int32(job.core))) {
	    job.status = uint8(jobStateCodes.REFUNDED); /* Important to check already refunded job or not */
	    job.jobOwner.transfer(netOwned); /* Pay back netOwned to client */
	    return false;
	}

	clusterContract[msg.sender].receivedAmount += amountToGain;

	job.status = uint8(jobStateCodes.COMPLETED); /* Prevents double spending */

	msg.sender.transfer(amountToGain);        /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(netOwned - amountToGain); /* Gained ether transferred to the client */

	/*emit*/ LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (netOwned - amountToGain), block.timestamp, resultIpfsHash, storageID);
	return true;
    }
    /* registerUser function registers a clients (msg.sender's) to eBlocBroker. It also updates userData. */
    function registerUser(string userEmail, string fID, string miniLockID, string ipfsAddress, string orcid, string githubUserName)
	public returns (bool success)
    {
	userContract[msg.sender].blockReadFrom = block.number;
	userContract[msg.sender].orcid         = orcid;

	/*emit*/ LogUser(msg.sender, userEmail, fID, miniLockID, ipfsAddress, orcid, githubUserName);
	return true;
    }

    function authenticateORCID(string orcid) isOwner(msg.sender)
	public returns (bool success)
    {
	verifyOrcid[orcid] = 1;
	return true;
    }

    /* registerCluster function registers a provider's (msg.sender's) cluster to eBlocBroker. */
    function registerCluster(uint32 coreNumber, string clusterEmail, string fID, string miniLockID, uint coreMinutePrice, string ipfsAddress)
	public returns (bool success)
    {
	Lib.clusterData storage cluster = clusterContract[msg.sender];
	if (cluster.blockReadFrom != 0 && cluster.isRunning)
	    revert();

	if (cluster.blockReadFrom != 0 && !cluster.isRunning) {
	    clusterAddresses[cluster.clusterAddressesID] = msg.sender;
	    cluster.update(coreMinutePrice, coreNumber);
	    cluster.isRunning = true;
	} else {
	    cluster.constructCluster(uint32(clusterAddresses.length), coreMinutePrice, coreNumber);
	    clusterAddresses.push(msg.sender); /* In order to obtain list of clusters */
	}

	/*emit*/ LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID, coreMinutePrice, ipfsAddress);
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
    function updateCluster(uint32 coreNumber, string clusterEmail, string fID, string miniLockID, uint coreMinutePrice, string ipfsAddress)
	public returns (bool success)
    {
	Lib.clusterData storage cluster = clusterContract[msg.sender];
	if (cluster.blockReadFrom == 0)
	    revert();

	clusterContract[msg.sender].update(coreMinutePrice, coreNumber);

	/*emit*/ LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID, coreMinutePrice, ipfsAddress);
	return true;
    }

    /* submitJob function performs a job submission to eBlocBroker by a client. */
    function submitJob(address clusterAddress, string jobKey, uint32 core, string jobDesc, uint32 coreMinuteGas, uint8 storageID)
	coreMinuteGas_storageID_check(coreMinuteGas, storageID) isZero(core) public payable
	returns (bool success)
    {
	Lib.clusterData storage cluster = clusterContract[clusterAddress];

	if (!cluster.isRunning                                         ||
	        msg.value < cluster.coreMinutePrice * coreMinuteGas * core ||
	    bytes(jobKey).length > 255                                 || // Max length is 255, becuase it will used as a filename at cluster
	    !isUserExist(msg.sender)                                   ||
	        verifyOrcid[userContract[msg.sender].orcid] == 0           ||
	    core > cluster.receiptList.coreNumber)
	    revert();

	cluster.jobStatus[jobKey].push(Lib.status({
		status:          uint8(jobStateCodes.PENDING),
			core:            core,                    // Requested Core value
			coreMinuteGas:   coreMinuteGas,           //
			jobOwner:        msg.sender,
			received:        msg.value,
			coreMinutePrice: cluster.coreMinutePrice, //
			startTime:       0
			}
		));
	/*emit*/ LogJob(clusterAddress, jobKey, cluster.jobStatus[jobKey].length-1, storageID, jobDesc);

	return true;
    }

    /* setJobStatus function sets the job's state (stateID) which is obtained from Slurm. */
    function setJobStatus(string jobKey, uint32 index, uint8 stateID, uint startTime) isBehindBlockTimeStamp(startTime) public
	stateID_check(stateID) returns (bool success)
    {
	Lib.status storage job = clusterContract[msg.sender].jobStatus[jobKey][index]; /* Used as a pointer to a storage */
	if (job.status == uint8(jobStateCodes.COMPLETED) ||
	    job.status == uint8(jobStateCodes.REFUNDED)  ||
	    job.status == uint8(jobStateCodes.RUNNING)) /* Cluster can sets job's status as RUNNING and its startTime only one time */
	    revert();

	job.status = stateID;
	if (stateID == uint8(jobStateCodes.RUNNING))
	    job.startTime = startTime;

	/*emit*/ LogSetJob(msg.sender, jobKey, index, startTime);
	return true;
    }

    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* getClusterAddresses} contract call returns a list of registered cluster Ethereum addresses. */
    function getClusterAddresses() public view
	returns (address[])
    {
	return clusterAddresses;
    }

    // isOrcIdVerified() function checks whether or not the given ORCID iD is already authenticated in eBlocBroker.
    function isOrcIdVerified(string orcid) public view
	returns (uint32)
    {
	return verifyOrcid[orcid];
    }

    /* getUserInfo function returns the enrolled user's
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event.
       It takes Ethereum address of the user (userAddress), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address userAddress) public view
	returns(uint, string)
    {
	if (userContract[userAddress].blockReadFrom != 0)
	    return (userContract[userAddress].blockReadFrom, userContract[userAddress].orcid);
    }

    /* getClusterInfo} function returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses. */
    function getClusterInfo(address clusterAddress) public view
	returns(uint, uint, uint)
    {
	if (clusterContract[clusterAddress].blockReadFrom != 0)
	    return (clusterContract[clusterAddress].blockReadFrom, clusterContract[clusterAddress].receiptList.coreNumber, clusterContract[clusterAddress].coreMinutePrice);
	else
	    return (0, 0, 0);
    }

    // getClusterReceivedAmount() function returns cluster provider's earned mon\-ey amount in Wei.
    // It takes a cluster's Ethereum address (clusterAddress) as parameter.
    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint)
    {
	return clusterContract[clusterAddress].receivedAmount;
    }

    function getJobSize(address clusterAddress, string jobKey) public view
	returns (uint)

    {
	if (clusterContract[msg.sender].blockReadFrom == 0)
	    revert();
	return clusterContract[clusterAddress].jobStatus[jobKey].length;
    }

    // getJobInfo function returns various information about the submitted job such as the hash of output files generated by IPFS,
    //   UNIX timestamp on job's start time, received Wei value from the client etc.
    function getJobInfo(address clusterAddress, string jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, uint, address)
    {
	Lib.status memory job = clusterContract[clusterAddress].jobStatus[jobKey][index];

	return (job.status, job.core, job.startTime, job.received, job.coreMinutePrice, job.coreMinuteGas, job.jobOwner);
    }

    // getDeployedBlockNumber() function returns the contract's deployed block number.
    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return deployedBlockNumber;
    }

    // getOwner() function returns the owner of the contract.
    function getOwner() public view
	returns (address)
    {
	return owner;
    }

    /* isClusterExist function checks whether or not the given Ethereum address of the provider (clusterAddress) is already registered in eBlocBroker. */
    function isClusterExist(address clusterAddress) public view
	returns (bool)
    {
	if (clusterContract[clusterAddress].blockReadFrom != 0)
	    return true;
	return false;
    }

    /* isUserExistfunction checks whether or not the given Ethereum address of the provider (userAddress) is already registered in eBlocBroker. */
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
    /* LogJob event records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint index,
		 uint8 storageID,
		  string desc
		 );

    /* LogReceipt event records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address clusterAddress,
		     string jobKey,
		     uint index,
		     address recipient,
		     uint received,
		     uint returned,
		     uint endTime,
		     string resultIpfsHash,
		          uint8 storageID
		     );

    /* LogCluster event records the registered clusters' registered information under registerCluster() method call.  (fID stands for federationCloudId) */
    event LogCluster(address clusterAddress,
		     uint32 coreNumber,
		     string clusterEmail,
		     string fID,
		     string miniLockID,
		     uint coreMinutePrice,
		          string ipfsAddress
		     );

    /* LogUser event records the registered users' registered information under registerUser method call.*/
    event LogUser(address userAddress,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string orcid,
		    string githubUserName
		  );

    /* LogRefund event records the refunded jobs' information under refund() method call. */
    event LogCancelRefund(address clusterAddress,
			  string jobKey,
			    uint32 index
			  );

    /* LogSetJob event records the updated jobs' information under setJobStatus() method call. */
    event LogSetJob(address clusterAddress,
		    string jobKey,
		    uint32 index,
		        uint startTime
		    );
}
