pragma solidity ^0.4.7;
import "./eBlocBrokerLib.sol";
import "./ReceiptLib.sol";

contract eBlocBroker {
    uint  deployedBlockNumber;
    function eBlocBroker(){ deployedBlockNumber = block.number; }
    enum JobStateCodes { Null, COMPLETED, PENDING, RUNNING }

    using eBlocBrokerLib for eBlocBrokerLib.data;
    using eBlocBrokerLib for eBlocBrokerLib.Status;
    using ReceiptLib     for ReceiptLib.intervalNode;

    eBlocBrokerLib.data             list;
    address[]            memberAddresses;

    mapping(address => eBlocBrokerLib.data)       clusterContract;

    function refundMe( address clusterAddr, string ipfsHash, uint32 index ) returns(bool){
	eBlocBrokerLib.Status jobStatus = clusterContract[clusterAddr].jobStatus[ipfsHash][index]; //if does not exist throws anyway.
	if( msg.sender != jobStatus.jobOwner ||
	    jobStatus.receiptFlag   == '1'
	    ) throw; //we understand that it didn't completed yet.

	if( jobStatus.status == uint8(JobStateCodes.PENDING) ) //status: queued
	    msg.sender.send(jobStatus.received);
	else if( (block.timestamp - jobStatus.startTimeStamp)  > jobStatus.coreMinuteGas * 60 + 600 )
	    msg.sender.send(jobStatus.received);

	jobStatus.receiptFlag = '1'; //only get refunded 1 time.
	//kill job on the slurm side.
	//TODO: event olarak yollaman gerekiyor.
	//clusterContract[clusterAddr].cancelledJob.push( eBlocBrokerLib.job({hash: ipfsHash, index: index, storageType: storageType }) );
	return true;
    }

    function receiptCheck( string jobKey, uint32 index, uint32 jobRunTimeMinute, string ipfsHashOut, uint8 storageType, uint endTimeStamp )
	public returns( bool success ){ //timeToPayBack.
	eBlocBrokerLib.Status jobStatus = clusterContract[msg.sender].jobStatus[jobKey][index]; //!clusterContract[clusterAddr].isExist  patlar
	uint netOwed                    = jobStatus.received;
	uint amountToGain               = jobStatus.coreMinutePrice * jobRunTimeMinute * jobStatus.core;

	if( amountToGain > netOwed                             ||
	    jobStatus.receiptFlag   == '1'                     ||
	    ( storageType == 0 && bytes(ipfsHashOut).length != 46 ) ||
	    endTimeStamp > block.timestamp )
	    throw;

	clusterContract[msg.sender].receiptList.receiptCheck( jobStatus.startTimeStamp, endTimeStamp, int32(jobStatus.core) );

	//  Gained by the cluster.               Gained by the client
	if( !msg.sender.send( amountToGain ) && !jobStatus.jobOwner.send( netOwed - amountToGain) ) throw;

	clusterContract[msg.sender].receivedAmount += amountToGain;

	jobStatus.status       = uint8(JobStateCodes.COMPLETED);
	jobStatus.receiptFlag  = '1';
	LogReceipt( msg.sender, jobKey, index, jobStatus.jobOwner, jobStatus.received, (netOwed - amountToGain),
		    block.timestamp, ipfsHashOut, storageType );
	return true;
    }

    function registerCluster(uint32 coreLimit, bytes clusterName, bytes fID, bytes miniLockId, uint price, bytes32 ipfsId)
	public returns(bool success){
	eBlocBrokerLib.data cluster = clusterContract[msg.sender];
	if( (cluster.isExist && cluster.isRunning == true) ||
	    bytes(fID).length         > 128                ||
	    bytes(clusterName).length > 128                ||
	    (bytes(miniLockId).length != 0 && bytes(miniLockId).length != 45)
	    ) throw;

	if( cluster.isExist && cluster.isRunning == false ){
	    memberAddresses[cluster.memberAddressesID] = msg.sender; //0 lanmisti yenden tanimla. liste de gozuksun.
	    cluster.update(clusterName, fID, miniLockId, price, coreLimit, ipfsId);     //update
	    cluster.isRunning = true;                               //running true olur.
	}
	else{
	    cluster.construct(clusterName, fID, miniLockId, uint32(memberAddresses.length), price, coreLimit, ipfsId);
	    memberAddresses.push( msg.sender ); //in order to obtain list of clusters.
	}
	return true;
    }

    function deregisterCluster() public returns( bool success ){//Locks the access to the Cluster. Only cluster owner could stop it.
	if( !clusterContract[msg.sender].isExist          && //if does not exist
	    clusterContract[msg.sender].isRunning == false   //if already false.
	    )  throw;

	delete memberAddresses[ clusterContract[msg.sender].memberAddressesID ];
	clusterContract[msg.sender].isRunning   = false; //Cluster wont accept any more jobs.
	return true;
    }

    //Combine all set operations to update ClusterInfo, it will save up some gas usage.
    function updateCluster( uint32 coreLimit, bytes clusterName, bytes fID, bytes miniLockId, uint price, bytes32 ipfsId)
	public returns(bool success){
	if( bytes(clusterName).length > 64 )
	    throw;
	clusterContract[msg.sender].update(clusterName, fID, miniLockId, price, coreLimit, ipfsId);
	return true;
    }

    //works as inserBack (FIFO).
    function submitJob( address clusterAddr, string jobKey, uint32 core, string jobDesc, uint32 coreMinuteGas, uint8 storageType, string miniLockId )
	payable public returns( bool success ){
	eBlocBrokerLib.data cluster = clusterContract[clusterAddr];

	if( coreMinuteGas == 0                                            ||
	    msg.value < cluster.coreMinutePrice * coreMinuteGas * core    ||
	    coreMinuteGas > 11520                                         || //9 day limit
	    cluster.isRunning == false                                    ||
	    core > cluster.receiptList.coreLimit                          ||
	    bytes(jobDesc).length > 64                                    ||
	    core == 0                                                     ||
	    ( storageType == 0 && bytes(jobKey).length     != 46 )        || //Could I trust that user enters a valid hash.//may be unneeded.
	    ( storageType == 2 && bytes(miniLockId).length != 45 )           //Could I trust that user enters a valid hash.//may be unneeded.
	    ) throw;

	LogJob( clusterAddr, jobKey, cluster.jobStatus[jobKey].length, storageType, miniLockId, jobDesc );

	cluster.jobStatus[jobKey].push(
				       eBlocBrokerLib.Status({
					   status:          uint8(JobStateCodes.PENDING),
						   core:            core,
						   coreMinuteGas:   coreMinuteGas,
						   jobOwner:        msg.sender,
						   received:        msg.value,
						   coreMinutePrice: cluster.coreMinutePrice,  
						   startTimeStamp:  0,
						   receiptFlag:    '0'
						   }) );
	return true;
    }

    function getClusterAddresses() constant returns ( address[] ){
	return memberAddresses; //returns all addresses all together.
    }

    function getClusterInfo( address clusterAddr ) constant returns( bytes, bytes, bytes, uint, uint, bytes32 ) {
	return ( clusterContract[clusterAddr].name, 
		 clusterContract[clusterAddr].federationCloudId, 
		 clusterContract[clusterAddr].clusterMiniLockId,
		 clusterContract[clusterAddr].receiptList.coreLimit, 
		 clusterContract[clusterAddr].coreMinutePrice, 
		 clusterContract[clusterAddr].ipfsId );
    }

    function getClusterReceivedAmount(address clusterAddr) constant returns ( uint ){
	return clusterContract[clusterAddr].receivedAmount;
    }

    function setJobStatus( string jobKey, uint32 index, uint8 stateId, uint startTimeStamp )
	public returns( bool success ){
	eBlocBrokerLib.Status jS = clusterContract[msg.sender].jobStatus[jobKey][index];
	if( jS.receiptFlag   == '1' || stateId > 15 || startTimeStamp > block.timestamp )
	    throw;

	if( stateId != 0 ) {
	    jS.status         = stateId;
	    jS.startTimeStamp = startTimeStamp;
	}
	return true;
    }

    function getJobInfo(address clusterAddr, string jobKey, uint index) constant
	public returns( uint8, uint32, uint, uint, uint, uint ) {
	eBlocBrokerLib.Status jS = clusterContract[clusterAddr].jobStatus[jobKey][index];

	return ( jS.status, jS.core, jS.startTimeStamp, jS.received, jS.coreMinutePrice, jS.coreMinuteGas );
	//0        1            2                 3               4              5              6
    }

    function getJobSize(address clusterAddr, string jobKey) constant returns ( uint ) {
	if( !clusterContract[msg.sender].isExist) throw;
	return clusterContract[clusterAddr].jobStatus[jobKey].length;
    }

    function getDeployedBlockNumber() constant returns ( uint ) { return deployedBlockNumber; }
    event    LogJob( address cluster, string jobKey, uint index, uint8 storageType, string miniLockId, string desc );
    event    LogReceipt( address cluster, string jobKey, uint index, address recipient, uint recieved, uint returned,
			 uint endTime, string ipfsHashOut, uint8 storageType );

    function testCallStack() returns ( int ){ return 1; }
}

/*
  function getClusterReceiptSize(address clusterAddr) constant returns(uint32) {
  return clusterContract[clusterAddr].receiptList.getReceiptListSize();
  }
  function getClusterReceiptNode(address clusterAddr, uint32 index) constant returns(uint32, int32 ) {
  return clusterContract[clusterAddr].receiptList.print_index(index);
  }
*/
//jobStatus.returned     = netOwed - amountToGain; //Log
