pragma solidity ^0.4.17; import "./Lib.sol";

contract eBlocBroker {
    
    uint  deployedBlockNumber; /* The block number that was obtained when contract is deployed */

    enum jobStateCodes {
	NULL,      //0
	COMPLETED, //1 /* Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,  //2 /* Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,   //3
	RUNNING    //4	
    }
	
    function eBlocBroker() public
    {
	deployedBlockNumber = block.number;
    }
    
    using Lib for Lib.intervalNode;
    using Lib for Lib.clusterData;
    using Lib for Lib.userData;
    using Lib for Lib.status;

    address[] clusterAddresses; // A dynamically-sized array of `address` structs
    address[]    userAddresses; // A dynamically-sized array of `address` structs

    mapping(address => Lib.clusterData) clusterContract;
    mapping(address => Lib.userData)       userContract;   

    modifier coreMinuteGas_storageID_check(uint32 coreMinuteGas, uint8 storageID) {	
	require(!(coreMinuteGas == 0 || coreMinuteGas > 1440) && storageID < 5); /* coreMinuteGas is maximum 1 day */
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

    /* refund function pays back to client if a job is still on pending status or is not completed one hour after its required time. */
    function refund(address clusterAddress, string jobKey, uint32 index) public returns (bool)
    {
	/* If 'clusterAddress' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index' 
	   is not mapped to a job , this will throw automatically and revert all changes */
	Lib.status storage job = clusterContract[clusterAddress].jobStatus[jobKey][index];
	if (msg.sender != job.jobOwner ||
	    job.status == uint8(jobStateCodes.COMPLETED) || job.status == uint8(jobStateCodes.REFUNDED)
	    ) /* Job has not completed yet */
	    revert(); 

	if (job.status == uint8(jobStateCodes.PENDING) || /* If job have not been started running*/
	   (job.status == uint8(jobStateCodes.RUNNING) && (block.timestamp - job.startTime) > job.coreMinuteGas * 60 + 3600)) { /* Job status remain running after one hour that job should have completed */
	    msg.sender.transfer(job.received);
	    
	    job.status = uint8(jobStateCodes.REFUNDED); /* Prevents double spending */
	    LogRefund(clusterAddress, jobKey, index); /* scancel log */
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
	
	uint netOwed      = job.received;
	uint amountToGain = job.coreMinutePrice * job.core * jobRunTimeMinute;

	if((amountToGain > netOwed) || job.status == uint8(jobStateCodes.COMPLETED) || job.status == uint8(jobStateCodes.REFUNDED) ) 
	    revert();
	
	if (!clusterContract[msg.sender].receiptList.receiptCheck(job.startTime, endTime, int32(job.core))) { 	    
	    job.status = uint8(jobStateCodes.REFUNDED); /* Important to check already refunded job or not */
	    job.jobOwner.transfer(netOwed); /* Pay back netOwned to client */
	    return false;
	}
	
	clusterContract[msg.sender].receivedAmount += amountToGain;

	job.status = uint8(jobStateCodes.COMPLETED); /* Prevents double spending */

	msg.sender.transfer(amountToGain); 	       /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(netOwed - amountToGain); /* Gained ether transferred to the client */
	
	LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (netOwed - amountToGain), block.timestamp, resultIpfsHash, storageID);
	return true;
    }
    /* registerUser function registers a clients (msg.sender's) to eBlocBroker. It also updates userData. */
    function registerUser(string userEmail, string fID, string miniLockID, string ipfsAddress, string orcID, string githubUserName) 
	public returns (bool success)
    {
	userContract[msg.sender].blockReadFrom = block.number;
	
	LogUser(msg.sender, userEmail, fID, miniLockID, ipfsAddress, orcID, githubUserName);
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
	
	LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID, coreMinutePrice, ipfsAddress);
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
	
	LogCluster(msg.sender, coreNumber, clusterEmail, fID, miniLockID, coreMinutePrice, ipfsAddress);
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
	    core > cluster.receiptList.coreNumber)
	    revert();
	
	cluster.jobStatus[jobKey].push(Lib.status({
 		        status:          uint8(jobStateCodes.PENDING),
			core:            core,                    //
			coreMinuteGas:   coreMinuteGas,           //
			jobOwner:        msg.sender,              //
			received:        msg.value,               //
			coreMinutePrice: cluster.coreMinutePrice, //
			startTime:       0                        //
			}
		));
	
	LogJob(clusterAddress, jobKey, cluster.jobStatus[jobKey].length-1, storageID, jobDesc);

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

	LogSetJob(msg.sender, jobKey, index, startTime);
	return true;
    }
    
    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* getClusterAddresses} contract call returns a list of registered cluster Ethereum addresses. */
    function getClusterAddresses() public view
	returns (address[])
    {
	return clusterAddresses; 
    }

    /* getUserInfo function returns the enrolled user's 
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event. 
       It takes Ethereum address of the user (userAddress), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address userAddress) public view
	returns(uint)
    {
	if (userContract[userAddress].blockReadFrom != 0)	    
	    return (userContract[userAddress].blockReadFrom);
	else
	    return (0);
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

    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint)
    {
	return clusterContract[clusterAddress].receivedAmount;
    }

    /* getJobInfo function returns various information about the submitted job such as the hash of output files generated by IPFS,                       
       UNIX timestamp on job's start time, received Wei value from the client etc.
    */
    function getJobInfo(address clusterAddress, string jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, uint, address)
    {
	Lib.status memory job = clusterContract[clusterAddress].jobStatus[jobKey][index];

	return (job.status, job.core, job.startTime, job.received, job.coreMinutePrice, job.coreMinuteGas, job.jobOwner);   
    }

    function getJobSize(address clusterAddress, string jobKey) public view
	returns (uint)
    {
	if (clusterContract[msg.sender].blockReadFrom == 0)
	    revert();
	return clusterContract[clusterAddress].jobStatus[jobKey].length;
    }

    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return deployedBlockNumber;
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

    /* -----------------------------------------------------EVENTS---------------------------------------------------------*/
    /* LogJob event records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address cluster,
		 string jobKey,
		 uint index,
		 uint8 storageID,		 
		 string desc
		 );
    
    /* LogReceipt event records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address cluster,
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
    event LogCluster(address cluster,
		     uint32 coreNumber,
		     string clusterEmail,
		     string fID,
		     string miniLockID,
		     uint coreMinutePrice,
		     string ipfsAddress
		     );
    
    /* LogUser event records the registered users' registered information under registerUser method call.*/
    event LogUser(address cluster,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string orcID,
		  string githubUserName
		  );
    
    /* LogRefund event records the refunded jobs' information under refund() method call. */
    event LogRefund(address clusterAddress,
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
