pragma solidity ^0.4.17;

import "./eBlocBrokerLib.sol";
import "./ReceiptLib.sol";

contract eBlocBroker {
    uint  deployedBlockNumber;

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
    
    using eBlocBrokerLib for eBlocBrokerLib.data;
    using eBlocBrokerLib for eBlocBrokerLib.Status;
    using ReceiptLib     for ReceiptLib.intervalNode;

    eBlocBrokerLib.data             list;
    address[]            memberAddresses;

    mapping(address => eBlocBrokerLib.data) clusterContract;   

    modifier coreMinuteGas_StorageType_check(uint32 coreMinuteGas, uint8 storageType) {	
	require( !(coreMinuteGas == 0 || coreMinuteGas > 11520) && (storageType < 4)); /* coreMinuteGas has maximum 9 days */
	_ ;
    }

    modifier deregisterClusterCheck() {
	require(clusterContract[msg.sender].isExist && clusterContract[msg.sender].isRunning); 
	_ ;
    }

    modifier blocktimePassed(uint time) {
	require(time <= block.timestamp); 
	_ ;
    }

    modifier isZero(uint32 input) {
	require(input != 0); 
	_ ;
    }

    function refundMe(address clusterAddr, string jobKey, uint32 index) public returns(bool)
    {
	eBlocBrokerLib.Status memory job = clusterContract[clusterAddr].jobStatus[jobKey][index]; /* If does not exist EVM revert()s error */
	if (msg.sender != job.jobOwner || job.receiptFlag)
	    revert(); /* Job has not completed yet */

	if (job.status == uint8(JobStateCodes.PENDING)) 
	    msg.sender.transfer(job.received);
	else if ((block.timestamp - job.startTime)  > job.coreMinuteGas * 60 + 600)
	    msg.sender.transfer(job.received);

	job.receiptFlag = true; /* Prevents double spending */
	return true;
    }

    function receiptCheck(string jobKey, uint32 index, uint32 jobRunTimeMinute, string ipfsHashOut, uint8 storageType, uint endTime)
	blocktimePassed(endTime) public returns (bool success) /* Payback to client and server */
    { 
	eBlocBrokerLib.Status memory job = clusterContract[msg.sender].jobStatus[jobKey][index]; /* If clusterContract[msg.sender] isExist returns false EVM revert() */
	uint netOwed                     = job.received;
	uint amountToGain                = job.coreMinutePrice * jobRunTimeMinute * job.core;

	if(amountToGain > netOwed || job.receiptFlag) //endTime > block.timestamp ) done.	    
	    revert();
	
	if (!clusterContract[msg.sender].receiptList.receiptCheck(job.startTime, endTime, int32(job.core))) { 	    
	    job.jobOwner.transfer(netOwed); /* Pay back netOwned to client */
	    job.receiptFlag  = true; /* Important to check already paid job or not */	    
	    return false;
	}
	
	msg.sender.transfer( amountToGain); 	       /* Gained by the cluster */
	job.jobOwner.transfer(netOwed - amountToGain); /* Gained by the client */

	clusterContract[msg.sender].receivedAmount += amountToGain;

	job.status       = uint8(JobStateCodes.COMPLETED);
	job.receiptFlag  = true; 

	LogReceipt(msg.sender, jobKey, index, job.jobOwner, job.received, (netOwed - amountToGain ), block.timestamp, ipfsHashOut, storageType);
	return true;
    }

    function registerCluster(uint32 coreNumber, string clusterName, string fID, string miniLockId, uint price, bytes32 ipfsId) 
	public returns (bool success)
    {
	eBlocBrokerLib.data cluster = clusterContract[msg.sender];
	if (cluster.isExist && cluster.isRunning)
	    revert();
	
	if (cluster.isExist && !cluster.isRunning) {
	    memberAddresses[cluster.memberAddressesID] = msg.sender; 
	    cluster.update(clusterName, fID, miniLockId, price, coreNumber, ipfsId); 
	    cluster.isRunning = true; 
	} else {
	    cluster.construct(clusterName, fID, miniLockId, uint32(memberAddresses.length), price, coreNumber, ipfsId);
	    memberAddresses.push( msg.sender ); /* In order to obtain list of clusters */
	}	
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
    function updateCluster(uint32 coreNumber, string clusterName, string fID, string miniLockId, uint price, bytes32 ipfsId)
	public returns (bool success)
    {
	clusterContract[msg.sender].update(clusterName, fID, miniLockId, price, coreNumber, ipfsId);
	return true;
    }
   
    /* Works as inserBack on linkedlist (FIFO) */
    function submitJob(address clusterAddr, string jobKey, uint32 core, string jobDesc, uint32 coreMinuteGas, uint8 storageType, string miniLockId)
	coreMinuteGas_StorageType_check(coreMinuteGas, storageType) isZero(core) payable public returns (bool success)
    {
	eBlocBrokerLib.data cluster = clusterContract[clusterAddr];
	
	if (msg.value < cluster.coreMinutePrice * coreMinuteGas * core ||	   
	    !cluster.isRunning                                         || 
	    core > cluster.receiptList.coreNumber)
	    revert();

	cluster.jobStatus[jobKey].push( eBlocBrokerLib.Status({
		        status:          uint8(JobStateCodes.PENDING),
			core:            core,
			coreMinuteGas:   coreMinuteGas,
			jobOwner:        msg.sender,
			received:        msg.value,
			coreMinutePrice: cluster.coreMinutePrice,  
			startTime:       0,
			receiptFlag:     false}
			));
	
	LogJob(clusterAddr, jobKey, cluster.jobStatus[jobKey].length, storageType, miniLockId, jobDesc);
	return true;
    }

    function setJobStatus(string jobKey, uint32 index, uint8 stateId, uint startTime) blocktimePassed(startTime) public returns (bool success)
    {
	eBlocBrokerLib.Status jS = clusterContract[msg.sender].jobStatus[jobKey][index]; /* used as a pointer to a storage */
	if (jS.receiptFlag || stateId > 15 )
	    revert();

	if (stateId != 0) {
	    jS.status    = stateId;
	    jS.startTime = startTime;
	}	
	return true;
    }

    event LogJob    (address cluster, string jobKey, uint index, uint8 storageType, string miniLockId, string desc);
    event LogReceipt(address cluster, string jobKey, uint index, address recipient, uint recieved, uint returned, uint endTime, string ipfsHashOut, uint8 storageType);
    
    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* Returns all register cluster addresses */
    function getClusterAddresses() public view returns (address[])
    {
	return memberAddresses; 
    }

    function getClusterInfo(address clusterAddr) public view returns(string, string, string, uint, uint, bytes32)
    {
	return (clusterContract[clusterAddr].name, 
		clusterContract[clusterAddr].federationCloudId, 
		clusterContract[clusterAddr].clusterMiniLockId,
		clusterContract[clusterAddr].receiptList.coreNumber, 
		clusterContract[clusterAddr].coreMinutePrice, 
		clusterContract[clusterAddr].ipfsId);
    }

    function getClusterReceivedAmount(address clusterAddr) public view returns (uint)
    {
	return clusterContract[clusterAddr].receivedAmount;
    }

    function getJobInfo(address clusterAddr, string jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, uint)
    {
	eBlocBrokerLib.Status memory jS = clusterContract[clusterAddr].jobStatus[jobKey][index];

	return (jS.status, jS.core, jS.startTime, jS.received, jS.coreMinutePrice, jS.coreMinuteGas);   
    }

    function getJobSize(address clusterAddr, string jobKey) public view returns (uint)
    {
	if( !clusterContract[msg.sender].isExist)
	    revert();
	return clusterContract[clusterAddr].jobStatus[jobKey].length;
    }

    function getDeployedBlockNumber() public view  returns (uint)
    {
	return deployedBlockNumber;
    }

    function getClusterReceiptSize(address clusterAddr) public view returns(uint32)
    {
	return clusterContract[clusterAddr].receiptList.getReceiptListSize();
    }

    function getClusterReceiptNode(address clusterAddr, uint32 index) public view returns (uint256, int32)
    {
	return clusterContract[clusterAddr].receiptList.printIndex(index);
    }
}
