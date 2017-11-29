//TODO: storageType github add.
//TODO: decode/encode string lz-string
//TODO: desc in uint ipfs.

pragma solidity ^0.4.17;
import "./eBlocBrokerLib.sol";
import "./ReceiptLib.sol";

contract eBlocBroker {
    uint  deployedBlockNumber;
    function eBlocBroker()
    {
	deployedBlockNumber = block.number;
    }
    enum JobStateCodes { Null, COMPLETED, PENDING, RUNNING }

    using eBlocBrokerLib for eBlocBrokerLib.data;
    using eBlocBrokerLib for eBlocBrokerLib.Status;
    using ReceiptLib     for ReceiptLib.intervalNode;

    eBlocBrokerLib.data             list;
    address[]            memberAddresses;

    mapping(address => eBlocBrokerLib.data) clusterContract;   

    modifier coreMinuteGas_StorageType_Check(uint32 coreMinuteGas, uint8 storageType) {	
	require( !(coreMinuteGas == 0 || coreMinuteGas > 11520) && (storageType < 3) ); /* coreMinuteGas has maximum 9 days */
	_ ;
    }

    modifier deregisterClusterCheck() {
	require( clusterContract[msg.sender].isExist && clusterContract[msg.sender].isRunning ); 
	_ ;
    }
    
    function refundMe(address clusterAddr, string jobKeyHash, uint32 index ) public returns(bool)
    {
	eBlocBrokerLib.Status job = clusterContract[clusterAddr].jobStatus[jobKeyHash][index]; /* If does not exist EVM throws error */
	if (msg.sender != job.jobOwner || job.receiptFlag)
	    throw; /* Job has not completed yet */

	if (job.status == uint8(JobStateCodes.PENDING)) 
	    msg.sender.send(job.received);
	else if ((block.timestamp - job.startTimeStamp)  > job.coreMinuteGas * 60 + 600)
	    msg.sender.send(job.received);

	job.receiptFlag = true; /* Prevents double spending */
	//kill job on the slurm side.
	//TODO: event olarak yollaman gerekiyor.
	//clusterContract[clusterAddr].cancelledJob.push( eBlocBrokerLib.job({hash: ipfsHash, index: index, storageType: storageType }) );
	return true;
    }

    function receiptCheck(string jobKeyHash, uint32 index, uint32 jobRunTimeMinute, string ipfsHashOut, uint8 storageType, uint endTimeStamp)
	public returns (bool success) /* Payback to client and server */
    { 
	eBlocBrokerLib.Status job = clusterContract[msg.sender].jobStatus[jobKeyHash][index]; /* If clusterContract[msg.sender] isExist is false EVM throws error */
	uint netOwed              = job.received;
	uint amountToGain         = job.coreMinutePrice * jobRunTimeMinute * job.core;

	if( amountToGain > netOwed ||
	    job.receiptFlag        ||
	    endTimeStamp > block.timestamp
	    //( storageType == 0 && bytes(ipfsHashOut).length != 46 ) || //TODO: Do this on upper level.
	    ) throw;
	if (!clusterContract[msg.sender].receiptList.receiptCheck( job.startTimeStamp, endTimeStamp, int32(job.core))) { 	    
	    if (!job.jobOwner.send(netOwed)) /* Pay back netOwned to client */
		throw;
	    job.receiptFlag  = true; /* Important to check already paid job or not */
	    
	    return false;
	}
	/*   Gained by the cluster.               Gained by the client */
	if (!msg.sender.send( amountToGain ) && !job.jobOwner.send( netOwed - amountToGain))
	    throw;

	clusterContract[msg.sender].receivedAmount += amountToGain;

	job.status       = uint8(JobStateCodes.COMPLETED);
	job.receiptFlag  = true; 
	LogReceipt( msg.sender, jobKeyHash, index, job.jobOwner, job.received, (netOwed - amountToGain ), block.timestamp, ipfsHashOut, storageType );
	return true;
    }

    function registerCluster(uint32 coreNumber, string clusterName, string fID, string miniLockId, uint price, bytes32 ipfsId) 
	public returns (bool success)
    {
	eBlocBrokerLib.data cluster = clusterContract[msg.sender];
	if (cluster.isExist && cluster.isRunning)
	    throw;
	
	if (cluster.isExist && !cluster.isRunning){
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
	delete memberAddresses[ clusterContract[msg.sender].memberAddressesID ];
	clusterContract[msg.sender].isRunning = false; /* Cluster wont accept any more jobs */
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateCluster( uint32 coreNumber, string clusterName, string fID, string miniLockId, uint price, bytes32 ipfsId)
	public returns (bool success)
    {
	clusterContract[msg.sender].update(clusterName, fID, miniLockId, price, coreNumber, ipfsId);
	return true;
    }

    
    //TODO: miniLockId save for each user.
    /* Works as inserBack on linkedlist (FIFO) */
    function submitJob(address clusterAddr, string jobKey, uint32 core, string jobDesc, uint32 coreMinuteGas, uint8 storageType, string miniLockId)
	coreMinuteGas_StorageType_Check(coreMinuteGas, storageType) payable public returns (bool success)
    {
	eBlocBrokerLib.data cluster = clusterContract[clusterAddr];
	if (msg.value < cluster.coreMinutePrice * coreMinuteGas * core ||	   
	    !cluster.isRunning                                         || 
	    core == 0                                                  ||
	    core > cluster.receiptList.coreNumber)
	    throw;

	LogJob( clusterAddr, jobKey, cluster.jobStatus[jobKey].length, storageType, miniLockId, jobDesc );

	cluster.jobStatus[jobKey].push( eBlocBrokerLib.Status({
 		        status:          uint8(JobStateCodes.PENDING),
			core:            core,
			coreMinuteGas:   coreMinuteGas, //received / (coreMinutePrice * core) ... 5000 gas saved.
			jobOwner:        msg.sender,
			received:        msg.value,
			coreMinutePrice: cluster.coreMinutePrice,  
			startTimeStamp:  0,
			receiptFlag:     false 
			}) );
	
	return true;
    }

    function setJobStatus(string jobKey, uint32 index, uint8 stateId, uint startTimeStamp) public returns (bool success)
    {
	eBlocBrokerLib.Status jS = clusterContract[msg.sender].jobStatus[jobKey][index];
	if (jS.receiptFlag ||
	    stateId > 15 || startTimeStamp > block.timestamp) //TODO: carry to modifier.
	    throw;

	if (stateId != 0) {
	    jS.status         = stateId;
	    jS.startTimeStamp = startTimeStamp;
	}
	
	return true;
    }

    event LogJob    (address cluster, string jobKey, uint index, uint8 storageType, string miniLockId, string desc);
    event LogReceipt(address cluster, string jobKeyHash, uint index, address recipient, uint recieved, uint returned,
		     uint endTime, string ipfsHashOut, uint8 storageType);

    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */

    /* Returns all register cluster addresses */
    function getClusterAddresses() constant returns (address[])
    {
	return memberAddresses; 
    }

    function getClusterInfo(address clusterAddr) constant returns(string, string, string, uint, uint, bytes32)
    {
	return (clusterContract[clusterAddr].name, 
		clusterContract[clusterAddr].federationCloudId, 
		clusterContract[clusterAddr].clusterMiniLockId,
		clusterContract[clusterAddr].receiptList.coreNumber, 
		clusterContract[clusterAddr].coreMinutePrice, 
		clusterContract[clusterAddr].ipfsId);
    }

    function getClusterReceivedAmount(address clusterAddr) constant returns (uint)
    {
	return clusterContract[clusterAddr].receivedAmount;
    }

    function getJobInfo(address clusterAddr, string jobKey, uint index) constant
	returns (uint8, uint32, uint, uint, uint, uint)
    {
	eBlocBrokerLib.Status jS = clusterContract[clusterAddr].jobStatus[jobKey][index];

	return ( jS.status, jS.core, jS.startTimeStamp, jS.received, jS.coreMinutePrice, jS.coreMinuteGas );   
    }

    function getJobSize(address clusterAddr, string jobKey) constant returns (uint)
    {
	if( !clusterContract[msg.sender].isExist)
	    throw;
	return clusterContract[clusterAddr].jobStatus[jobKey].length;
    }

    function getDeployedBlockNumber() constant returns (uint)
    {
	return deployedBlockNumber;
    }

    function getClusterReceiptSize(address clusterAddr) constant returns(uint32)
    {
	return clusterContract[clusterAddr].receiptList.getReceiptListSize();
    }

    function getClusterReceiptNode(address clusterAddr, uint32 index) constant returns (uint256, int32)
    {
	return clusterContract[clusterAddr].receiptList.printIndex(index);
    }
    /*
    function testCallStack() returns (int)
    {
	return 1;
    } 
    */   
}
