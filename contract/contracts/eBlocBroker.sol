/*
  file:   eBlocBroker.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
//pragma experimental ABIEncoderV2;

import "./Lib.sol";
import "./eBlocBrokerInterface.sol";
import "./eBlocBrokerBase.sol";
import "./math/SafeMath.sol";

/* Contract Address: 0x */
/// @title eBlocBroker is a blockchain based autonomous computational resource broker.
contract eBlocBroker is eBlocBrokerInterface, eBlocBrokerBase {
    using SafeMath for uint256;
    
    using Lib for Lib.IntervalNode;
    using Lib for Lib.Cluster;
    using Lib for Lib.User;
    using Lib for Lib.Status; 
    using Lib for Lib.StateCodes;
    using Lib for Lib.DataInfo;
    using Lib for Lib.ClusterInfo;

    /**
       @notice eBlocBroker constructor
       @dev Sets contract's deployed block number and the owner of the contract. 	   	  
    */
    constructor() public
    {
	deployedBlock = block.number;
	owner = msg.sender; /* msg.sender is owner of the smart contract */	
    }

    /** 
	@notice 
	* Refund funds the complete amount to client if requested job is still in the pending state or
	is not completed one hour after its required time.
	If the job is in the running state, it triggers LogRefund event on the blockchain, 
	which will be caught by the cluster in order to cancel the job. 	  
	@param clusterAddress | Ethereum Address of the cluster
	@param _key  | Uniqu ID for the given job
	@param index | The index of the job
	@param jobID | ID of the job to identify under workflow
	@return bool 
    */    
    function refund(address clusterAddress, string memory _key, uint32 index, uint32 jobID) public
	returns (bool)
    {
	/* If 'clusterAddress' is not mapped on 'cluster' array  or its '_key' and 'index'
	   is not mapped to a job , this will throw automatically and revert all changes */	
	Lib.Status storage job  = cluster[clusterAddress].jobStatus[_key][index];
	Lib.Job storage jobInfo = job.jobs[jobID];
	    
	require(msg.sender == job.jobOwner &&
		jobInfo.status != Lib.StateCodes.COMPLETED &&
		jobInfo.status != Lib.StateCodes.REFUNDED
		);
	
	if (jobInfo.status == Lib.StateCodes.PENDING || /* If job have not been started running*/
	    (jobInfo.status == Lib.StateCodes.RUNNING &&
	     (block.timestamp - job.jobs[jobID].startTime) > job.jobs[jobID].executionTimeMin * 60 + 3600)) { /* Job status remain running after one hour that job should have completed */
		msg.sender.transfer(job.received);
		jobInfo.status = Lib.StateCodes.REFUNDED; /* Prevents double spending */
		emit LogRefund(clusterAddress, _key, index, jobID); /* scancel log */
		return true;
	}
	else if (jobInfo.status == Lib.StateCodes.RUNNING) {
	    jobInfo.status = Lib.StateCodes.CANCELLED;
	    emit LogRefund(clusterAddress, _key, index, jobID); /* scancel log */
	    return true;
	}
	else
	    revert();
    }

    /**
       @notice        
       * Following function is a general-purpose mechanism for performing payment withdrawal
       by the cluster provider and paying of unused core, cache, and dataTransfer usage cost 
       back to the client
    */
    function receiptCheck(string memory _key,
			  uint32 index,
			  uint32 jobID,
			  uint32 executionTimeMin,
			  bytes32 resultIpfsHash,
			  uint32 endTime,			  
			  uint[] memory dataTransfer) public
    {
	require(endTime <= block.timestamp, "Behind timestamp");
	
	/* If "msg.sender" is not mapped on 'cluster' struct or its "_key" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes 
	*/		
	Lib.Status storage job  = cluster[msg.sender].jobStatus[_key][index];	

	require(executionTimeMin <= job.jobs[jobID].executionTimeMin &&        // Cluster cannot request more time of the job that is already requested
		dataTransfer[0].add(dataTransfer[1]) <= (job.dataTransferIn.add(job.dataTransferOut)) // Cluster cannot request more than the job's given dataTransferOut amount
		);
	
	Lib.ClusterInfo memory info = cluster[msg.sender].info[job.pricesSetBlockNum];
		
	uint amountToGain;
	uint amountToRefund;
	
	if (job.cacheCost > 0) {
	    require(dataTransfer[0] <= job.dataTransferIn);     // Cluster cannot request more dataTransferIn that is already requested
	    
	    amountToGain   = info.priceCache * dataTransfer[0]; //cacheCost
	    amountToRefund = info.priceCache * (job.dataTransferIn - dataTransfer[0]); //cacheCostRefund
	    
	    if (amountToGain.add(amountToRefund) > job.cacheCost)
		revert();
	    	    
	    delete job.cacheCost; // Prevents additional cacheCost to be requested, can request cache cost only one time
	}
	
	if (dataTransfer[1] > 0 && job.dataTransferOut > 0) {
	    amountToRefund += info.priceDataTransfer * (job.dataTransferOut.sub(dataTransfer[1]));
	    delete job.dataTransferOut; // Prevents additional dataTransfer to be request for dataTransferOut
	}
	
	amountToGain +=
	    info.priceCoreMin * job.jobs[jobID].core * executionTimeMin + // computationalCost       	    
	    info.priceDataTransfer * (dataTransfer[0] + dataTransfer[1]);    // dataTransferCost
	
	/* computationalCostRefund */
	amountToRefund += info.priceCoreMin * job.jobs[jobID].core * (job.jobs[jobID].executionTimeMin - executionTimeMin);
	if (job.dataTransferIn > 0) {
	    amountToRefund += info.priceDataTransfer * (job.dataTransferIn - dataTransfer[0]); // dataTransferRefund
	    delete job.dataTransferIn; // Prevents additional cacheCost to be requested
	}
 
	if (amountToGain + amountToRefund > job.received ||
	    job.jobs[jobID].status == Lib.StateCodes.COMPLETED ||
	    job.jobs[jobID].status == Lib.StateCodes.REFUNDED)
	    revert();

	if (!cluster[msg.sender].receiptList.receiptCheck(job.jobs[jobID], uint32(endTime) + uint64(uint64(info.availableCore) << 32))) {
	    job.jobs[jobID].status = Lib.StateCodes.REFUNDED; /* Important to check already refunded job or not */	    
	    job.jobOwner.transfer(job.received); /* Pay back newOwned(job.received) to the client, full refund */
		
	    emit LogReceipt(msg.sender, _key, index, jobID, job.jobOwner, 0, job.received, block.timestamp,
			    resultIpfsHash, dataTransfer[0], dataTransfer[1]);
	    return;
	}

	if (job.jobs[jobID].status == Lib.StateCodes.CANCELLED)
	    job.jobs[jobID].status = Lib.StateCodes.REFUNDED;  /* Prevents double spending */
	else    
	    job.jobs[jobID].status = Lib.StateCodes.COMPLETED; /* Prevents double spending */
	
	cluster[msg.sender].received += amountToGain;	
	msg.sender.transfer(amountToGain); /* Gained amount is transferred to the cluster */

	job.received -= amountToRefund;
	job.jobOwner.transfer(amountToRefund); /* Unused core and bandwidth is refundedn back to the client */

	emit LogReceipt(msg.sender, _key, index, jobID, job.jobOwner, amountToGain, amountToRefund, block.timestamp, resultIpfsHash,
			dataTransfer[0], dataTransfer[1]);
	return;
    }
        
    function receiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) isClusterExists() public	
	returns (bool) {
	Lib.Cluster storage cluster = cluster[msg.sender];	
	
	if (cluster.jobSt[sourceCodeHash].receivedBlock + cluster.jobSt[sourceCodeHash].cacheDuration < block.number) {
	    msg.sender.transfer(cluster.receivedForStorage[jobOwner][sourceCodeHash]); //storagePayment
	    emit LogStoragePayment(msg.sender, cluster.receivedForStorage[jobOwner][sourceCodeHash]);	    
	    cluster.receivedForStorage[jobOwner][sourceCodeHash] = 0;
	    return true;
	}
	return false;
    }
    
    /*
      function extentStorageTime(address clusterAddress, string memory sourceCodeHash, uint cacheTime) public
      returns (bool) {
      require(cacheTime > 0);
      Lib.Cluster storage cluster = cluster[msg.sender];

      if (cluster.jobSt[sourceCodeHash].receivedBlock + cluster.jobSt[sourceCodeHash].cacheDuration >= block.number) {
      cluster.jobSt[sourceCodeHash].cacheDuration += cacheTime * 240;
      }
      }
    */

    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates User */
    function registerUser(string memory userEmail,
			  string memory federatedCloudID,
			  string memory miniLockID,
			  string memory ipfsAddress,
			  string memory githubUserName,
			  string memory whisperPublicKey) public 
	returns (bool)
    {
	user[msg.sender].committedBlock = uint32(block.number);
	emit LogUser(msg.sender, userEmail, federatedCloudID, miniLockID, ipfsAddress, githubUserName, whisperPublicKey);
	return true;
    }

    /* Registers a provider's (msg.sender's) cluster to eBlocBroker */
    function registerCluster(string memory email,
			     string memory federatedCloudID,
			     string memory miniLockID,
			     uint32 availableCore,
			     uint32 priceCoreMin,
			     uint32 priceDataTransfer,
			     uint32 priceStorage,
			     uint32 priceCache,
			     uint32 commitmentBlockDuration,
			     string memory ipfsAddress,
			     string memory whisperPublicKey) public isClusterRegistered()
	returns (bool)
    {
	require(availableCore > 0 &&
		priceCoreMin > 0  &&
		commitmentBlockDuration > 8 //1440 // Commitment duration should be one day
		);
	
	Lib.Cluster storage cluster = cluster[msg.sender];	
	require(!cluster.isRunning);
	
	cluster.info[block.number] = Lib.ClusterInfo({
         	    availableCore:      availableCore,
		    priceCoreMin:       priceCoreMin,
		    priceDataTransfer:  priceDataTransfer,
		    priceStorage:       priceStorage,
		    priceCache:         priceCache,
 		    commitmentBlockDuration: commitmentBlockDuration
		    });
	
	pricesSetBlockNum[msg.sender].push(uint32(block.number));	    
	cluster.constructCluster();
	clusterAddresses.push(msg.sender); // In order to obtain the list of clusters 

	emit LogClusterInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);	
	return true;
    }

    /* All set operations are combined to save up some gas usage */
    function updateClusterInfo(string memory email,
			       string memory federatedCloudID,
			       string memory miniLockID,
			       string memory ipfsAddress,
			       string memory whisperPublicKey) public isClusterExists()
	returns (bool)
    {
	emit LogClusterInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);
	return true;
    }       

    /* Pauses the access to the Cluster. Only cluster owner could stop it */
    function pauseCluster() public isClusterRunning()
	returns (bool)
    {
	cluster[msg.sender].isRunning = false; /* Cluster will not accept any more jobs */
	return true;
    }

    function unpauseCluster() public isClusterExists() whenClusterPaused()
	returns (bool)
    {
	cluster[msg.sender].isRunning = true; 
	return true;
    }

    /**
       @notice 
       * Update prices and available core number of the cluster
       @param availableCore | Available core number
       @param commitmentBlockDuration | Requred block number duration for prices to committed
       @param prices | Array of prices ([priceCoreMin, priceDataTransfer, priceStorage, priceCache]) 
       to update for the cluster
       @return bool success
    */    
    function updateClusterPrices(uint32 availableCore,
				 uint32 commitmentBlockDuration,
				 uint32[] memory prices) public isClusterExists()
	returns (bool)
    {
	require(availableCore > 0 &&
		prices[0] > 0     &&
		commitmentBlockDuration > 8 //1440 // Commitment duration should be one day
		);
	
	Lib.Cluster storage cluster = cluster[msg.sender];

	uint32[] memory clusterInfo = pricesSetBlockNum[msg.sender];
	uint32 _pricesSetBlockNum = clusterInfo[clusterInfo.length-1];
	if (_pricesSetBlockNum > block.number) { // Enters if already updated futher away of the committed block
	    cluster.info[uint32(_pricesSetBlockNum)] = Lib.ClusterInfo({
		availableCore:      availableCore,
			priceCoreMin:       prices[0],
			priceDataTransfer:  prices[1],
			priceStorage:       prices[2],
			priceCache:         prices[3],
			commitmentBlockDuration: commitmentBlockDuration
			});	   
	}
	else {
	    uint _commitmentBlockDuration = cluster.info[cluster.committedBlock].commitmentBlockDuration;	    
	    uint committedBlockNum = _pricesSetBlockNum + _commitmentBlockDuration; //future block number

	    if (committedBlockNum <= block.number) {
		committedBlockNum = (block.number - _pricesSetBlockNum) / _commitmentBlockDuration + 1;		
		committedBlockNum = _pricesSetBlockNum + committedBlockNum * _commitmentBlockDuration;
	    }

	    cluster.info[uint32(committedBlockNum)] = Lib.ClusterInfo({
		availableCore:      availableCore,
			priceCoreMin:       prices[0],
			priceDataTransfer:  prices[1],
			priceStorage:       prices[2],
			priceCache:         prices[3],
			commitmentBlockDuration: commitmentBlockDuration
			});

	    //if (clusterInfo[clusterInfo.length-1] != committedBlockNum)
	    pricesSetBlockNum[msg.sender].push(uint32(committedBlockNum));
	}
	return true;
    }
	    
    /**
     @notice 
     * Performs a job submission to eBlocBroker by the client
     *@param clusterAddress | The address of the cluster
     *@param _key  | Uniqu ID for the given job
     *@param index | The index of the job
     *@param core  | Array of core for the given jobs
     *@param executionTimeMin | Array of minute to execute for the given jobs
     *@param dataTransferIn  | Array of the sizes of the give data files
     *@param dataTransferOut  | Size of the data to retrive from the generated outputs
     *@param storageID_cacheType | StorageID and cacheTupe
     *@param cacheTime | Array of times to cache the data files
     *@param sourceCodeHash | Array of source code hashes
    */
    function submitJob(address   payable clusterAddress,
		       string    memory  _key,
		       uint16[]  memory  core,
		       uint16[]  memory  executionTimeMin,
		       uint32[]  memory  dataTransferIn,
		       uint32            dataTransferOut,		       
		       uint8[]   memory  storageID_cacheType,
		       uint32[]  memory  cacheTime,
		       bytes32[] memory  sourceCodeHash) public payable
    {
	require(clusterAddress != address(0), "Invalid address");

 	Lib.Cluster storage cluster = cluster[clusterAddress];
	
	require(sourceCodeHash.length > 0 &&
		cacheTime.length == sourceCodeHash.length &&
		sourceCodeHash.length == dataTransferIn.length &&
		core.length == executionTimeMin.length &&
		cluster.isRunning             &&
		storageID_cacheType[0] <= 4   &&
		bytes(_key).length <= 255     && // Max length is 255 for the filename 
		isUserExist(msg.sender)       &&
		bytes(user[msg.sender].orcID).length > 0 
		);
	
	uint32[] memory clusterInfo = pricesSetBlockNum[clusterAddress];
	
	uint priceBlockKey;
	if (clusterInfo[clusterInfo.length-1] > block.number) // If the cluster's price is updated on the future block
	    priceBlockKey = clusterInfo[clusterInfo.length-2];
	else
	    priceBlockKey = clusterInfo[clusterInfo.length-1];

	Lib.ClusterInfo memory info = cluster.info[priceBlockKey];
	
	uint sum;	
	uint storageCost;

	// Here "cacheTime[0]" used to store the calcualted cacheCost
	(sum, dataTransferIn[0], storageCost, cacheTime[0]) = _calculateCacheCost(clusterAddress, cluster, sourceCodeHash, dataTransferIn, dataTransferOut, cacheTime, info);	
	sum += _calculateComputationalCost(info, core, executionTimeMin);	

	require(msg.value >= sum);

	cluster.jobStatus[_key].push(Lib.Status({
    		        dataTransferIn:  dataTransferIn[0],
			dataTransferOut: dataTransferOut,
			jobOwner:        msg.sender,
			received:        msg.value - storageCost,
			pricesSetBlockNum: uint32(priceBlockKey),
			cacheCost: cacheTime[0]
			}
		));

	_saveCoreAndCoreMin(cluster, _key, core, executionTimeMin);

	priceBlockKey = cluster.jobStatus[_key].length - 1; // Here "priceBlockKey" used as temp variable to hold index value
	_logJobEvent(clusterAddress, _key, uint32(storageCost), storageID_cacheType[0], sourceCodeHash, storageID_cacheType[1]);
	
	return;
    }
	
    function updateJobReceivedBlocNumber(bytes32 sourceCodeHash) public
	returns (bool)
    {
	Lib.Cluster storage cluster = cluster[msg.sender]; //Only cluster can update receied job only to itself
	if (cluster.jobSt[sourceCodeHash].receivedBlock > 0)
 	    cluster.jobSt[sourceCodeHash].receivedBlock = uint32(block.number); //Cluster only update the block.number
	
	return true;
    }
    	
    /**
     *@dev Sets requested job's description.
     *@param clusterAddress The address of the cluster.
     *@param _key The string of the _key.
     *@param index The index of the job.
     */
    function setJobDescription(address clusterAddress, string memory _key, string memory jobDesc) public
	returns (bool)
    {
	if (msg.sender == cluster[clusterAddress].jobStatus[_key][0].jobOwner)
	    emit LogJobDescription(clusterAddress, _key, jobDesc);
	
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(string memory _key, uint32 index, uint32 jobID, Lib.StateCodes stateID, uint32 startTime)
	isBehindBlockTimeStamp(startTime) checkStateID(stateID) public
	returns (bool)
    {
	Lib.Job storage job = cluster[msg.sender].jobStatus[_key][index].jobs[jobID]; /* Used as a pointer to a storage */

	/* Cluster can sets job's status as RUNNING and its startTime only one time */
	require (job.status != Lib.StateCodes.COMPLETED &&
		 job.status != Lib.StateCodes.REFUNDED  &&
		 job.status != Lib.StateCodes.RUNNING,
		 "Not permitted");
		
	job.status = stateID;
	if (stateID == Lib.StateCodes.RUNNING)
	    job.startTime = startTime;

	emit LogSetJob(msg.sender, _key, index, jobID, startTime);
	return true;
    }

    /* ------------------------------------------------------------INTERNAL_FUNCTIONS---------------------------------------------------------------- */
    
    function _logJobEvent(address _addr, string memory _key, uint32 index, uint8 storageID, bytes32[] memory sourceCodeHash, uint8 cacheType) internal {
	emit LogJob(_addr, _key, index, storageID, sourceCodeHash, cacheType, msg.value);
    }

    function _saveCoreAndCoreMin(Lib.Cluster storage cluster, string memory _key, uint16[]  memory  core, uint16[]  memory  executionTimeMin) internal
    {
	Lib.Status storage status = cluster.jobStatus[_key][cluster.jobStatus[_key].length - 1];	
	for(uint i = 0; i < core.length; i++) {
	    status.jobs[i].core = core[i];    /* Requested core value for each job on the workflow*/
	    status.jobs[i].executionTimeMin = executionTimeMin[i]; 
	}
    }


    function _calculateComputationalCost(Lib.ClusterInfo memory info, uint16[]  memory  core, uint16[]  memory  executionTimeMin) internal
    	returns (uint sum)
    {
	uint256 executionTimeMinSum;
	for (uint i = 0; i < core.length; i++){
	    uint computationalCost = info.priceCoreMin * core[i] * executionTimeMin[i];
	    executionTimeMinSum = executionTimeMinSum.add(executionTimeMin[i]);
	    
	    require(core[i] <= info.availableCore &&
		    computationalCost > 0         &&
		    executionTimeMinSum <= 1440 // Total execution time of the workflow should be shorter than a day 
		    );
	    
	    sum = sum.add(computationalCost);
	}
	
	return sum;
    }

    function _calculateCacheCost(address payable clusterAddress,
				 Lib.Cluster storage cluster,
				 bytes32[] memory sourceCodeHash,
				 uint32[] memory dataTransferIn,
				 uint32 dataTransferOut,
				 uint32[] memory cacheTime,
				 Lib.ClusterInfo memory info) internal 
	returns (uint sum, uint32 _dataTransferIn, uint _storageCost, uint32 _cacheCost) {

	for (uint i = 0; i < sourceCodeHash.length; i++) {
	    Lib.JobStorageTime storage jobSt = cluster.jobSt[sourceCodeHash[i]];
	    uint _receivedForStorage = cluster.receivedForStorage[msg.sender][sourceCodeHash[i]];

	    if (jobSt.receivedBlock + jobSt.cacheDuration < block.number) { // Remaining time to cache is 0
		_dataTransferIn += dataTransferIn[i];

		if (cacheTime[i] > 0) { // Enter if the required time in hours to cache is not 0
		    if (_receivedForStorage > 0) {
			clusterAddress.transfer(_receivedForStorage); //storagePayment
			cluster.receivedForStorage[msg.sender][sourceCodeHash[i]] = 0;
			emit LogStoragePayment(clusterAddress, _receivedForStorage);	    
		    }
	    
		    jobSt.receivedBlock = uint32(block.number);
		    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
		    jobSt.cacheDuration = cacheTime[i] * 240;

		    uint _storageCostTemp = info.priceStorage * dataTransferIn[i] * cacheTime[i];
		    cluster.receivedForStorage[msg.sender][sourceCodeHash[i]] = _storageCostTemp;		    
		    _storageCost += _storageCostTemp;
		}
		else { // Data is not cached, communication cost should be applied
		    _cacheCost += info.priceCache * dataTransferIn[i]; // cacheCost
		}
	    }
	    else { //Data is provided by the cluster with its own price
	        Lib.DataInfo storage _dataInfo = cluster.providedData[sourceCodeHash[i]];
		if (_dataInfo.isExist) 
		    _storageCost += _dataInfo.price;
	    }
	}
	
	sum += info.priceDataTransfer * (_dataTransferIn + dataTransferOut) + _storageCost + _cacheCost;

	return (sum, uint32(_dataTransferIn), uint32(_storageCost), uint32(_cacheCost));
    }    

    /* ------------------------------------------------------------GETTERS------------------------------------------------------------------------- */
    /* Returns the enrolled user's
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event.
       It takes Ethereum address of the user (userAddress), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address userAddress) public view
	returns (uint, string memory)
    {
	if (user[userAddress].committedBlock > 0)
	    return (user[userAddress].committedBlock, user[userAddress].orcID);
    }
    
    /* Returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses
    */    
    function getClusterInfo(address clusterAddress) public view
	returns(uint32[7] memory){	
	uint32[]  memory clusterInfo = pricesSetBlockNum[clusterAddress];
	uint32[7] memory clusterPriceInfo;
	    
	uint32 _pricesSetBlockNum = clusterInfo[clusterInfo.length-1];
        if (_pricesSetBlockNum > block.number)
            _pricesSetBlockNum = clusterInfo[clusterInfo.length-2]; // Obtain the committed prices before the block number
	
	Lib.ClusterInfo memory _clusterPrices = cluster[clusterAddress].info[_pricesSetBlockNum];
	
	if (cluster[clusterAddress].committedBlock == 0)
	    return clusterPriceInfo;

	clusterPriceInfo[0] = _pricesSetBlockNum; 
	clusterPriceInfo[1] = _clusterPrices.availableCore;
	clusterPriceInfo[2] = _clusterPrices.priceCoreMin;	
	clusterPriceInfo[3] = _clusterPrices.priceDataTransfer;
	clusterPriceInfo[4] = _clusterPrices.priceStorage;
	clusterPriceInfo[5] = _clusterPrices.priceCache;	
	clusterPriceInfo[6] = _clusterPrices.commitmentBlockDuration;
	    
	return clusterPriceInfo;
    }
    

    /* Returns various information about the submitted job such as the hash of output files generated by IPFS,
       UNIX timestamp on job's start time, received Wei value from the client etc. 
    */
    function getJobInfo(address clusterAddress, string memory _key, uint32 index, uint jobID) public view
	returns (Lib.StateCodes, uint32, uint val, uint, uint, address, uint, uint)
    {
	val = cluster[clusterAddress].jobStatus[_key].length;
        if (val == 0 || val <= index)
	    return (Lib.StateCodes.SUBMITTED, 0, 0, 0, 0, address(0x0), 0, 0);
		
	Lib.Status storage job = cluster[clusterAddress].jobStatus[_key][index];
		
	return (job.jobs[jobID].status,
		job.jobs[jobID].core,
		job.jobs[jobID].startTime,
		job.received,
		job.jobs[jobID].executionTimeMin,
		job.jobOwner,
		job.dataTransferIn,
		job.dataTransferOut);
    }
    
    function getClusterPricesForJob(address clusterAddress, string memory _key, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.Status      memory job         = cluster[clusterAddress].jobStatus[_key][index];
	Lib.ClusterInfo memory clusterInfo = cluster[clusterAddress].info[job.pricesSetBlockNum];
	    
	return (clusterInfo.priceCoreMin,
		clusterInfo.priceDataTransfer,
		clusterInfo.priceStorage,
		clusterInfo.priceCache);
    }

    /* Returns a list of registered/updated cluster's block number */     
    function getClusterPricesBlockNumbers(address clusterAddress) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[clusterAddress];
    }

    /* Returns the contract's deployed block number */
    function getDeployedBlockNumber() external view
	returns (uint)
    {
	return deployedBlock;
    }

    /* Returns the owner of the contract */
    function getOwner() external view
	returns (address) {
	return owner;
    }

    function getJobSize(address clusterAddress, string memory _key) public view
	returns (uint)
    {
	require(cluster[msg.sender].committedBlock > 0);
	    
	return cluster[clusterAddress].jobStatus[_key].length;
    }

    /* Returns cluster provider's earned money amount in Wei.
       It takes a cluster's Ethereum address (clusterAddress) as parameter. 
    */
    function getClusterReceivedAmount(address clusterAddress) external view
	returns (uint)
    {
	return cluster[clusterAddress].received;
    }
	
    /* Returns a list of registered cluster Ethereum addresses */
    function getClusterAddresses() public view
	returns (address[] memory)
    {
	return clusterAddresses;
    }
	
    function getJobStorageTime(address clusterAddress, bytes32 sourceCodeHash) external view
	returns(uint, uint)
    {	    
	Lib.Cluster storage cluster = cluster[clusterAddress];
	
	return (cluster.jobSt[sourceCodeHash].receivedBlock,
		uint256(cluster.jobSt[sourceCodeHash].cacheDuration).div(240));
    }

    /* Checks whether or not the given Ethereum address of the provider (clusterAddress) 
       is already registered in eBlocBroker. 
    */
    function isClusterExist(address clusterAddress) external view
	returns (bool)
    {
	return cluster[clusterAddress].committedBlock > 0;
    }

    /* Checks whether or not the enrolled user's given ORCID iD is already authenticated in eBlocBroker */
    function isUserOrcIDVerified(address userAddress) external view
	returns (bool)
    {
	return bytes(user[userAddress].orcID).length > 0;
    }

    function authenticateOrcID(address userAddress, string memory orcID) onlyOwner() isOrcIDverified(userAddress) public
	returns (bool)
    {
	user[userAddress].orcID = orcID;
	return true;
    }

    /* Checks whether or not the given Ethereum address of the user (userAddress) 
       is already registered in eBlocBroker. 
    */
    function isUserExist(address userAddress) public view
	returns (bool)
    {
	return user[userAddress].committedBlock > 0;
    }
        
    function getReceiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) isClusterExists() external view
	returns (uint) {
	return cluster[msg.sender].receivedForStorage[jobOwner][sourceCodeHash];
    }

    /* Get contract balance */
    function getContractBalance() external view
	returns (uint)
    {
	return address(this).balance;
    }

    /* Used for tests */
    function getClusterSetBlockNumbers(address _addr) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[_addr];
    }

    /* Used for tests */
    function getClusterReceiptSize(address clusterAddress) external view
	returns (uint32)
    {
	return cluster[clusterAddress].receiptList.getReceiptListSize();
    }

    /* Used for tests */
    function getClusterReceiptNode(address clusterAddress, uint32 index) external view
	returns (uint256, int32)
    {
	return cluster[clusterAddress].receiptList.printIndex(index);
    }
}
