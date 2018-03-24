pragma solidity ^0.4.17;

import "./Library.sol";

contract eBlocBroker {    
    uint  deployedBlockNumber; /* The block number that was obtained when contract is deployed */

    enum JobStateCodes {
	Null,
	COMPLETED,
	PENDING,
	RUNNING
    }
	
    function eBlocBroker() public
    {
	deployedBlockNumber = block.number;
    }
    
    using Library for Library.intervalNode;
    using Library for Library.data;
    using Library for Library.status;

    Library.data list;
    address[] memberAddresses; // A dynamically-sized array of `address` structs

    mapping(address => Library.data) clusterContract;   

    modifier coreMinuteGas_StorageType_check(uint32 coreMinuteGas, uint8 storageType) {	
	require(!(coreMinuteGas == 0 || coreMinuteGas > 1440) && (storageType < 4)); /* coreMinuteGas is maximum 1 day */
	_ ;
    }

    modifier deregisterClusterCheck() {
	require(clusterContract[msg.sender].isExist && clusterContract[msg.sender].isRunning); 
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

    function refund(address clusterAddr, string jobKey, uint32 index) public returns (bool)
    {
	/* If 'clusterAddr' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index' 
	   is not mapped to a job , this will throw automatically and revert all changes */
	Library.status job = clusterContract[clusterAddr].jobStatus[jobKey][index];
	if (msg.sender != job.jobOwner || job.receiptFlag)
	    revert(); /* Job has not completed yet */

	if (job.status == uint8(JobStateCodes.PENDING)) 
	    msg.sender.transfer(job.received);
	else if ((block.timestamp - job.startTime) > job.coreMinuteGas * 60 + 3600) 
	    msg.sender.transfer(job.received);

	job.receiptFlag = true; /* Prevents double spending */

	LogRefund(clusterAddr, jobKey, index);
	return true;
    }

    function receiptCheck(string jobKey, uint32 index, uint32 jobRunTimeMinute, string ipfsHashOut, uint8 storageType, uint endTime)
	isBehindBlockTimeStamp(endTime) public returns (bool success) /* Payback to client and server */
    {
	/* If 'msg.sender' is not mapped on 'clusterContract' array  or its 'jobKey' and 'index' 
	   is not mapped to a job , this will throw automatically and revert all changes */
	Library.status job = clusterContract[msg.sender].jobStatus[jobKey][index];
	
	uint netOwed      = job.received;
	uint amountToGain = job.coreMinutePrice * jobRunTimeMinute * job.core;

	if((amountToGain > netOwed) || job.receiptFlag) 
	    revert();
	
	if (!clusterContract[msg.sender].receiptList.receiptCheck(job.startTime, endTime, int32(job.core))) { 	    
	    job.receiptFlag  = true; /* Important to check already paid job or not */
	    job.jobOwner.transfer(netOwed); /* Pay back netOwned to client */
	    return false;
	}
	
	clusterContract[msg.sender].receivedAmount += amountToGain;

	job.status      = uint8(JobStateCodes.COMPLETED);
	job.receiptFlag = true; /* Prevents double spending */

	msg.sender.transfer(amountToGain); 	       /* Gained ether transferred to the cluster */
	job.jobOwner.transfer(netOwed - amountToGain); /* Gained ether transferred to the client */
	
	LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (netOwed - amountToGain), block.timestamp, ipfsHashOut, storageType);
	return true;
    }

    function registerCluster(uint32 coreNumber, string clusterName, string fID, string miniLockID, uint coreMinutePrice, string ipfsAddress) 
	public returns (bool success)
    {
	Library.data cluster = clusterContract[msg.sender];
	if (cluster.isExist && cluster.isRunning)
	    revert();
	
	if (cluster.isExist && !cluster.isRunning) {
	    memberAddresses[cluster.memberAddressesID] = msg.sender; 
	    cluster.update(coreMinutePrice, coreNumber); 
	    cluster.isRunning = true; 
	} else {
	    cluster.constructCluster(uint32(memberAddresses.length), coreMinutePrice, coreNumber);
	    memberAddresses.push(msg.sender); /* In order to obtain list of clusters */
	}
	
	LogCluster(msg.sender, coreNumber, clusterName, fID, miniLockID, coreMinutePrice, ipfsAddress);
	return true;
    }

    /* Locks the access to the Cluster. Only cluster owner could stop it */
    function deregisterCluster() public returns (bool success) 
    {
	delete memberAddresses[clusterContract[msg.sender].memberAddressesID];
	clusterContract[msg.sender].isRunning = false; /* Cluster wont accept any more jobs */
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateCluster(uint32 coreNumber, string clusterName, string fID, string miniLockID, uint coreMinutePrice, string ipfsAddress)
	public returns (bool success)
    {
	clusterContract[msg.sender].update(coreMinutePrice, coreNumber);
	
	LogCluster(msg.sender, coreNumber, clusterName, fID, miniLockID, coreMinutePrice, ipfsAddress);
	return true;
    }
   
    function submitJob(address clusterAddr, string jobKey, uint32 core, string jobDesc, uint32 coreMinuteGas, uint8 storageType, string miniLockID)
	coreMinuteGas_StorageType_check(coreMinuteGas, storageType) isZero(core) public payable
	returns (bool success)
    {
	Library.data cluster = clusterContract[clusterAddr];
	
	if (msg.value < cluster.coreMinutePrice * coreMinuteGas * core ||	   
	    !cluster.isRunning                                         || 
	    core > cluster.receiptList.coreNumber)
	    revert();

	cluster.jobStatus[jobKey].push( Library.status({
		status:          uint8(JobStateCodes.PENDING),
			core:            core,
			coreMinuteGas:   coreMinuteGas,
			jobOwner:        msg.sender,
			received:        msg.value,
			coreMinutePrice: cluster.coreMinutePrice,  
			startTime:       0,
			receiptFlag:     false}
		));
	
	LogJob(clusterAddr, jobKey, cluster.jobStatus[jobKey].length-1, storageType, miniLockID, jobDesc);
	return true;
    }

    function setJobStatus(string jobKey, uint32 index, uint8 stateId, uint startTime) isBehindBlockTimeStamp(startTime) public
	returns (bool success)
    {
	Library.status jS = clusterContract[msg.sender].jobStatus[jobKey][index]; /* used as a pointer to a storage */
	if (jS.receiptFlag || stateId > 15)
	    revert();

	if (stateId != 0) {
	    jS.status    = stateId;
	    jS.startTime = startTime;
	}

	LogSetJob(msg.sender, jobKey, index);
	return true;
    }
    
    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* Returns all registered cluster's Ethereum addresses */    
    function getClusterAddresses() public view
	returns (address[])
    {
	return memberAddresses; 
    }

    function getClusterInfo(address clusterAddr) public view
	returns(uint, uint, uint)
    {
	if (clusterContract[clusterAddr].isExist)	    
	    return (clusterContract[clusterAddr].blockReadFrom, clusterContract[clusterAddr].receiptList.coreNumber, clusterContract[clusterAddr].coreMinutePrice);
	else
	    return (0, 0, 0);
    }

    function getClusterReceivedAmount(address clusterAddr) public view
	returns (uint)
    {
	return clusterContract[clusterAddr].receivedAmount;
    }

    function getJobInfo(address clusterAddr, string jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, uint)
    {
	Library.status memory jS = clusterContract[clusterAddr].jobStatus[jobKey][index];

	return (jS.status, jS.core, jS.startTime, jS.received, jS.coreMinutePrice, jS.coreMinuteGas);   
    }

    function getJobSize(address clusterAddr, string jobKey) public view
	returns (uint)
    {
	if(!clusterContract[msg.sender].isExist)
	    revert();
	return clusterContract[clusterAddr].jobStatus[jobKey].length;
    }

    function getDeployedBlockNumber() public view
	returns (uint)
    {
	return deployedBlockNumber;
    }

    function getClusterReceiptSize(address clusterAddr) public view
	returns (uint32)
    {
	return clusterContract[clusterAddr].receiptList.getReceiptListSize();
    }

    function getClusterReceiptNode(address clusterAddr, uint32 index) public view
	returns (uint256, int32)
    {
	return clusterContract[clusterAddr].receiptList.printIndex(index);
    }
    
    function isClusterExist(address clusterAddr) public view
	returns (bool)
    {
	if (clusterContract[clusterAddr].isExist)
	    return true;	
	return false;
    }

    /* ------------------------------------------------------------EVENTS------------------------------------------------------------------------- */
    // Log submitted jobs
    event LogJob    (address cluster, string jobKey, uint index, uint8 storageType, string miniLockID, string desc);
    
    // Log completed jobs' receipt
    event LogReceipt(address cluster, string jobKey, uint index, address recipient, uint recieved, uint returned, uint endTime, string ipfsHashOut, uint8 storageType);

    // Log cluster info (fID stands for federationCloudId)
    event LogCluster(address cluster, uint32 coreNumber, string clusterName, string fID, string miniLockID, uint coreMinutePrice, string ipfsAddress);

    // Log refund
    event LogRefund(address clusterAddr, string jobKey, uint32 index);

    // Log setJob
    event LogSetJob(address clusterAddr, string jobKey, uint32 index);
}
