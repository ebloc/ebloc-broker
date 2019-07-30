/*
  file:   eBlocBroker.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
//pragma experimental ABIEncoderV2;

import "./Lib.sol";
import "./math/SafeMath.sol";
import "./eBlocBrokerInterface.sol";
import "./eBlocBrokerBase.sol";

/**
 * @title eBlocBroker
 * @dev The eBlocBroker contract is a blockchain based autonomous 
 * computational resource broker.
 */
contract eBlocBroker is eBlocBrokerInterface, eBlocBrokerBase {
    
    using SafeMath32 for uint32;
    using SafeMath   for uint256;
 
    using Lib for Lib.IntervalNode;
    using Lib for Lib.Cluster;
    using Lib for Lib.User;
    using Lib for Lib.Status; 
    using Lib for Lib.JobStateCodes;
    using Lib for Lib.ClusterInfo;

    /**
     * @notice eBlocBroker constructor
     * @dev The eBlocBroker constructor sets the original `owner` of the contract to the sender
     * account.
     */
    constructor() public { owner = msg.sender; }

    /**
     * @dev Allows the current owner to transfer control of the contract to a newOwner.
     * @param newOwner The address to transfer ownership to.
     */
    function transferOwnership(address newOwner) public onlyOwner {
	require(newOwner != address(0));
	emit OwnershipTransferred(owner, newOwner);
	owner = newOwner;
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
    
    /** 
     *	@notice 
     * Refund funds the complete amount to client if requested job is still in the pending state or
     * is not completed one hour after its required time.
     * If the job is in the running state, it triggers LogRefund event on the blockchain, 
     * which will be caught by the cluster in order to cancel the job. 	  
     * @param clusterAddress | Ethereum Address of the cluster.
     * @param _key  | Uniqu ID for the given job.
     * @param index | The index of the job.
     * @param jobID | ID of the job to identify under workflow.
     * @return bool 
     */    
    function refund(address clusterAddress, string memory _key, uint32 index, uint32 jobID, bytes32[] memory sourceCodeHash) public
	returns (bool)
    {
	Lib.Cluster storage cluster = cluster[clusterAddress];

	/*
	  If 'clusterAddress' is not mapped on 'cluster' array  or its '_key' and 'index'
	  is not mapped to a job , this will throw automatically and revert all changes 
	*/	
	Lib.Status storage jobInfo = cluster.jobStatus[_key][index];
	Lib.Job    storage job = jobInfo.jobs[jobID];
		    
	require(msg.sender == jobInfo.jobOwner                  &&
		job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
		job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
		job.jobStateCode != Lib.JobStateCodes.CANCELLED &&
		jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash))
		);
	
	if (!cluster.isRunning                      || // If cluster stop running
	    job.jobStateCode == Lib.JobStateCodes.PENDING || // If job have not been started running
	    (job.jobStateCode == Lib.JobStateCodes.RUNNING &&
	     (now - jobInfo.jobs[jobID].startTime) > jobInfo.jobs[jobID].executionTimeMin * 60 + 1 hours))
	    /* job.jobStateCode remain running after one hour that job should have completed */
	    {
		job.jobStateCode = Lib.JobStateCodes.REFUNDED; /* Prevents double spending and re-entrancy attack */
		uint payment = jobInfo.received;
		jobInfo.received = 0;
		msg.sender.transfer(payment);		
	    }
	else if (job.jobStateCode == Lib.JobStateCodes.RUNNING) {
	    job.jobStateCode = Lib.JobStateCodes.CANCELLED;
	    for (uint256 i = 0; i < sourceCodeHash.length; i++)
		cluster.storagedData[jobInfo.jobOwner][sourceCodeHash[i]].isUsed = true;
	}
	else
	    revert();
	

	emit LogRefund(clusterAddress, _key, index, jobID); /* scancel log */
	return true;
    }

    /**
       @notice        
       * Following function is a general-purpose mechanism for performing payment withdrawal
       * by the cluster provider and paying of unused core, cache, and dataTransfer usage cost 
       * back to the client
       * @param _key  | Uniqu ID for the given job.
       * @param index | The index of the job.
       * @param jobID | ID of the job to identify under workflow.
       * @param executionTimeMin | Execution time in minutes of the completed job.
       * @param resultIpfsHash | Ipfs hash of the generated output files.
       * @param endTime | // End time of the executed job.
       * @param dataTransfer | 
       */	
    function receiptCheck(string memory _key, uint32 index, uint32 jobID, uint32 executionTimeMin, bytes32 resultIpfsHash, uint32 endTime, uint32[] memory dataTransfer, bytes32[] memory sourceCodeHash) public whenClusterRunning
    {
	require(endTime <= now, "Ahead now");

	/* If "msg.sender" is not mapped on 'cluster' struct or its "_key" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes 
	*/
	Lib.Cluster storage cluster = cluster[msg.sender];	
	Lib.Status  storage jobInfo = cluster.jobStatus[_key][index];

	require(jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash)) && // Provide sourceCodeHashes should be same as with the ones that are provided with the job
		executionTimeMin <= jobInfo.jobs[jobID].executionTimeMin && // Cluster cannot request more execution time of the job that is already requested
		dataTransfer[0].add(dataTransfer[1]) <= (jobInfo.dataTransferIn.add(jobInfo.dataTransferOut)) // Cluster cannot request more than the job's given dataTransferOut amount
		);
	
	Lib.ClusterInfo memory info = cluster.info[jobInfo.pricesSetBlockNum];
		
	uint amountToGain;
	uint amountToRefund;
	
	if (jobInfo.cacheCost > 0) {
	    // Cluster cannot request more dataTransferIn that is already requested
	    require(dataTransfer[0] <= jobInfo.dataTransferIn); 
	    
	    amountToGain   = info.priceCache * dataTransfer[0]; //cacheCost
	    amountToRefund = info.priceCache * (jobInfo.dataTransferIn - dataTransfer[0]); //cacheCostRefund

	    require(amountToGain.add(amountToRefund) <= jobInfo.cacheCost);
			    	    
	    delete jobInfo.cacheCost; // Prevents additional cacheCost to be requested, can request cache cost only one time
	}
	
	if (dataTransfer[1] > 0 && jobInfo.dataTransferOut > 0) {
	    amountToRefund += info.priceDataTransfer * (jobInfo.dataTransferOut.sub(dataTransfer[1]));
	    delete jobInfo.dataTransferOut; // Prevents additional dataTransfer to be request for dataTransferOut
	}
	
	amountToGain +=
	    info.priceCoreMin * jobInfo.jobs[jobID].core * executionTimeMin + // computationalCost       	    
	    info.priceDataTransfer * (dataTransfer[0] + dataTransfer[1]); // dataTransferCost
	
	// computationalCostRefund 
	amountToRefund += info.priceCoreMin * jobInfo.jobs[jobID].core * (jobInfo.jobs[jobID].executionTimeMin - executionTimeMin);
	if (jobInfo.dataTransferIn > 0) {
	    amountToRefund += info.priceDataTransfer * (jobInfo.dataTransferIn - dataTransfer[0]); // dataTransferRefund
	    delete jobInfo.dataTransferIn; // Prevents additional cacheCost to be requested
	}

	require(amountToGain + amountToRefund <= jobInfo.received               &&
		jobInfo.jobs[jobID].jobStateCode != Lib.JobStateCodes.COMPLETED &&
		jobInfo.jobs[jobID].jobStateCode != Lib.JobStateCodes.REFUNDED
		);

	if (!cluster.receiptList.receiptCheck(jobInfo.jobs[jobID], uint32(endTime), int32(info.availableCore))) {
	    jobInfo.jobs[jobID].jobStateCode = Lib.JobStateCodes.REFUNDED; // Important to check already refunded job or not, prevents double spending
	    jobInfo.jobOwner.transfer(jobInfo.received); // Pay back newOwned(jobInfo.received) to the client, full refund
	    delete jobInfo.received;
	    _logReceipt(_key, index, jobID, jobInfo.jobOwner, 0, jobInfo.received, resultIpfsHash, dataTransfer);
	    return;
	}
	
	if (jobInfo.jobs[jobID].jobStateCode == Lib.JobStateCodes.CANCELLED)
	    jobInfo.jobs[jobID].jobStateCode = Lib.JobStateCodes.REFUNDED;  // Prevents double spending
	else    
	    jobInfo.jobs[jobID].jobStateCode = Lib.JobStateCodes.COMPLETED; // Prevents double spending
		
	msg.sender.transfer(amountToGain); // Gained amount is transferred to the cluster 
	cluster.received += amountToGain; 
	jobInfo.jobOwner.transfer(amountToRefund); // Unused core and bandwidth is refundedn back to the client 
	jobInfo.received -= amountToRefund + amountToGain;
	
	for (uint256 i = 0; i < sourceCodeHash.length; i++)
	    cluster.storagedData[jobInfo.jobOwner][sourceCodeHash[i]].isUsed = true;
	
	_logReceipt(_key, index, jobID, jobInfo.jobOwner, amountToGain, amountToRefund, resultIpfsHash, dataTransfer);
	return;
    }
            
    function receiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) whenClusterRunning public	
	returns (bool)
    {
	Lib.Cluster storage cluster = cluster[msg.sender];

	require(cluster.jobSt[sourceCodeHash].receivedBlock.add(cluster.jobSt[sourceCodeHash].cacheDuration) < block.number);
	
	uint payment = cluster.storagedData[jobOwner][sourceCodeHash].received;
	delete cluster.storagedData[jobOwner][sourceCodeHash].received;
	cluster.received.add(payment);
	msg.sender.transfer(payment);
	emit LogStoragePayment(msg.sender, payment);

	return true;
    }
	
    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates User */
    function registerUser(string memory userEmail, string memory federatedCloudID, string memory miniLockID, string memory ipfsAddress, string memory githubUserName, string memory whisperPublicKey) public 
	returns (bool)
    {
	user[msg.sender].committedBlock = uint32(block.number);
	emit LogUser(msg.sender, userEmail, federatedCloudID, miniLockID, ipfsAddress, githubUserName, whisperPublicKey);
	return true;
    }

    /* Registers a provider's (msg.sender's) cluster to eBlocBroker */
    function registerCluster(string memory email, string memory federatedCloudID, string memory miniLockID, uint32 availableCore, uint32 priceCoreMin, uint32 priceDataTransfer, uint32 priceStorage, uint32 priceCache, uint32 commitmentBlockDuration, string memory ipfsAddress, string memory whisperPublicKey) public whenClusterNotRegistered
	returns (bool)
    {
	Lib.Cluster storage cluster = cluster[msg.sender];
	
	require(availableCore > 0 &&
		priceCoreMin > 0  &&
		commitmentBlockDuration > 8 && //1440 // Commitment duration should be one day
		!cluster.isRunning
		);
			
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
	clusterAddresses.push(msg.sender); 

	emit LogClusterInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);	
	return true;
    }

    function updateClusterInfo(string memory email, string memory federatedCloudID, string memory miniLockID, string memory ipfsAddress, string memory whisperPublicKey) public whenClusterRegistered
	returns (bool)
    {
	emit LogClusterInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);
	return true;
    }       

    
    function pauseCluster() public whenClusterRunning /* Pauses the access to the cluster. Only cluster owner could stop it */
	returns (bool)
    {
	cluster[msg.sender].isRunning = false; /* Cluster will not accept any more jobs */
	return true;
    }

    function unpauseCluster() public whenClusterRegistered whenClusterPaused
	returns (bool)
    {
	cluster[msg.sender].isRunning = true; 
	return true;
    }

    /**
     * @notice Update prices and available core number of the cluster
     * @param availableCore | Available core number.
     * @param commitmentBlockDuration | Requred block number duration for prices to committed.
     * @param prices | Array of prices ([priceCoreMin, priceDataTransfer, priceStorage, priceCache])
     *                 to update for the cluster.
     * @return bool success
     */    
    function updateClusterPrices(uint32 availableCore, uint32 commitmentBlockDuration, uint32[] memory prices) public whenClusterRegistered
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
	    cluster.info[uint32(_pricesSetBlockNum)] =
		Lib.ClusterInfo({
		    availableCore:           availableCore,
			    priceCoreMin:            prices[0],
			    priceDataTransfer:       prices[1],
			    priceStorage:            prices[2],
			    priceCache:              prices[3],
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

	    pricesSetBlockNum[msg.sender].push(uint32(committedBlockNum));
	}
	
	return true;
    }

    function registerData(bytes32 sourceCodeHash, uint price) public whenClusterRegistered
    {
	/* Always increment price of the data by 1 before storing it. By default if price == 0, data does not exist.
	   If price == 1, it's an existing data that costs nothing. If price > 1, it's an existing data that costs give price.
	*/	
	cluster[msg.sender].registeredData[sourceCodeHash] = price.add(1);
    }

    /**
       @notice 
       * Performs a job submission to eBlocBroker by the client
       * @param clusterAddress | The address of the cluster
       * @param _key  | Uniqu ID for the given job
       * @param core  | Array of core for the given jobs
       * @param executionTimeMin | Array of minute to execute for the given jobs
       * @param dataTransferIn  | Array of the sizes of the give data files
       * @param dataTransferOut  | Size of the data to retrive from the generated outputs
       * @param storageID_cacheType | StorageID and cacheTupe
       * @param cacheTime | Array of times to cache the data files
       * @param sourceCodeHash | Array of source code hashes
       */
    function submitJob(address payable clusterAddress, string memory _key, uint16[] memory core, uint16[] memory executionTimeMin, uint32[] memory dataTransferIn, uint32 dataTransferOut, uint8[] memory storageID_cacheType, uint32[] memory cacheTime, bytes32[] memory sourceCodeHash) public payable
    {
	// require(clusterAddress != address(0), "Invalid address");

 	Lib.Cluster storage cluster = cluster[clusterAddress];

	require(cluster.isRunning                              && // Cluster must be running
		sourceCodeHash.length > 0                      &&
		cacheTime.length == sourceCodeHash.length      &&
		sourceCodeHash.length == dataTransferIn.length &&
		core.length == executionTimeMin.length &&		
		storageID_cacheType[0] <= 4   &&
		bytes(_key).length <= 255     && // Maximum _key length is 255 that will be used as folder name
		isUserExists(msg.sender)      &&
		bytes(user[msg.sender].orcID).length > 0 
		);

	uint32[] memory clusterInfo = pricesSetBlockNum[clusterAddress];
	
	uint priceBlockKey;
	if (clusterInfo[clusterInfo.length - 1] > block.number) // If the cluster's price is updated on the future block
	    priceBlockKey = clusterInfo[clusterInfo.length-2];
	else
	    priceBlockKey = clusterInfo[clusterInfo.length-1];

	Lib.ClusterInfo memory info = cluster.info[priceBlockKey];
	
	uint sum;	
	uint storageCost;

	// Here "cacheTime[0]" used to store the calcualted cacheCost
	(sum, dataTransferIn[0], storageCost, cacheTime[0]) = _calculateCacheCost(clusterAddress, cluster, sourceCodeHash, dataTransferIn, dataTransferOut, cacheTime, info);	
	sum = sum.add(_calculateComputationalCost(info, core, executionTimeMin));	

	require(msg.value >= sum);

	// Here returned "priceBlockKey" used as temp variable to hold pushed index value of the jobStatus struct
	priceBlockKey = _registerJob(cluster, _key, sourceCodeHash, storageCost, dataTransferIn[0], dataTransferOut, uint32(priceBlockKey), cacheTime[0]);
	
	_saveCoreAndCoreMin(cluster, _key, core, executionTimeMin, priceBlockKey);
	_logJobEvent(clusterAddress, _key, uint32(priceBlockKey), sourceCodeHash, storageID_cacheType);	
	return;
    }
    
    /**
     *@dev Updated data's received block number with block number
     *@param sourceCodeHash | Source-code hash of the requested data
     */	
    function updateDataReceivedBlock(bytes32 sourceCodeHash) public
	returns (bool)
    {
	Lib.Cluster storage cluster = cluster[msg.sender]; //Only cluster can update receied job only to itself
	if (cluster.jobSt[sourceCodeHash].receivedBlock > 0)
 	    cluster.jobSt[sourceCodeHash].receivedBlock = uint32(block.number); //Cluster only update the block.number
	
	return true;
    }
    	
    /**
     * @dev Sets requested job's description.
     * @param clusterAddress | The address of the cluster
     * @param _key | The string of the _key
     * @param jobDesc Description of the job
     */
    function setJobDescription(address clusterAddress, string memory _key, string memory jobDesc) public
	returns (bool)
    {
	if (msg.sender == cluster[clusterAddress].jobStatus[_key][0].jobOwner)
	    emit LogJobDescription(clusterAddress, _key, jobDesc);
	
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(string memory _key, uint32 index, uint32 jobID, Lib.JobStateCodes jobStateCode, uint32 startTime) public
	whenBehindNow(startTime) validJobStateCode(jobStateCode) 
	returns (bool)
    {
	Lib.Job storage job = cluster[msg.sender].jobStatus[_key][index].jobs[jobID]; /* Used as a pointer to a storage */

	/* Cluster can sets job's status as RUNNING and its startTime only one time */
	require (job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
		 job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
		 job.jobStateCode != Lib.JobStateCodes.CANCELLED &&
		 job.jobStateCode != Lib.JobStateCodes.RUNNING,
		 "Not permitted");	    
			    
	if (jobStateCode == Lib.JobStateCodes.RUNNING && job.startTime == 0)
	    job.startTime = startTime;
		
	job.jobStateCode = jobStateCode;
	emit LogSetJob(msg.sender, _key, index, jobID, startTime);
	return true;
    }
    
    function authenticateOrcID(address requester, string memory orcID) onlyOwner whenOrcidNotVerified(requester) public
	returns (bool)
    {
	user[requester].orcID = orcID;
	return true;
    }

    /* --------------------------------------------INTERNAL_FUNCTIONS-------------------------------------------- */

    function _registerJob(Lib.Cluster storage cluster, string memory _key, bytes32[] memory sourceCodeHash, uint storageCost, uint32 dataTransferIn, uint32 dataTransferOut, uint32 jobIndex, uint32 cacheCost) internal
	returns (uint)
    {
	//bytes32 _keccak256Key = keccak256(abi.encodePacked(_key));
	
	return cluster.jobStatus[_key].push(Lib.Status({
		dataTransferIn:    dataTransferIn,
			dataTransferOut:   dataTransferOut,
			jobOwner:          tx.origin,
			received:          msg.value - storageCost,
			pricesSetBlockNum: jobIndex,
			cacheCost:         cacheCost,
			sourceCodeHash:    keccak256(abi.encodePacked(sourceCodeHash))
			}
		)) - 1;
    }

    function _saveCoreAndCoreMin(Lib.Cluster storage cluster, string memory _key, uint16[] memory core, uint16[] memory executionTimeMin, uint index) internal
    {
	Lib.Status storage status = cluster.jobStatus[_key][index];	
	for(uint256 i = 0; i < core.length; i++) {
	    status.jobs[i].core = core[i];    /* Requested core value for each job on the workflow*/
	    status.jobs[i].executionTimeMin = executionTimeMin[i]; 
	}
    }

    function _calculateComputationalCost(Lib.ClusterInfo memory info, uint16[] memory  core, uint16[]  memory  executionTimeMin) internal
    	returns (uint sum)
    {
	uint256 executionTimeMinSum;
	for (uint256 i = 0; i < core.length; i++) {
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

    function _calculateCacheCost(address payable clusterAddress, Lib.Cluster storage cluster, bytes32[] memory sourceCodeHash, uint32[] memory dataTransferIn, uint32 dataTransferOut, uint32[] memory cacheTime, Lib.ClusterInfo memory info) internal
	returns (uint sum, uint32 _dataTransferIn, uint _storageCost, uint32 _cacheCost)
    {
	for (uint256 i = 0; i < sourceCodeHash.length; i++) {
	    Lib.JobStorageTime storage jobSt = cluster.jobSt[sourceCodeHash[i]];
	    uint _receivedForStorage = cluster.storagedData[msg.sender][sourceCodeHash[i]].received;

	    if (jobSt.receivedBlock + jobSt.cacheDuration < block.number) { // Remaining time to cache is 0
		_dataTransferIn = _dataTransferIn.add(dataTransferIn[i]);

		if (cacheTime[i] > 0) { // Enter if the required time in hours to cache is not 0
		    if (_receivedForStorage > 0) {
			// TODO: check
			clusterAddress.transfer(_receivedForStorage); //storagePayment
			delete cluster.storagedData[msg.sender][sourceCodeHash[i]].received;
			emit LogStoragePayment(clusterAddress, _receivedForStorage);	    
		    }
	    
		    jobSt.receivedBlock = uint32(block.number);
		    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
		    jobSt.cacheDuration = cacheTime[i] * 240;

		    uint _storageCostTemp = info.priceStorage * dataTransferIn[i] * cacheTime[i];
		    cluster.storagedData[msg.sender][sourceCodeHash[i]].received = uint248(_storageCostTemp);		    
		    _storageCost = _storageCost.add(_storageCostTemp);
		}
		else // Data is not cached, communication cost should be applied
		    _cacheCost += info.priceCache * dataTransferIn[i]; // cacheCost
	    }
	    else { //Data is provided by the cluster with its own price
	        uint256 _dataPrice = cluster.registeredData[sourceCodeHash[i]];
		if (_dataPrice > 1) 
		    _storageCost += _dataPrice;
	    }
	}
	
	sum += info.priceDataTransfer * (_dataTransferIn + dataTransferOut) + _storageCost + _cacheCost;
	return (sum, uint32(_dataTransferIn), uint32(_storageCost), uint32(_cacheCost));
    }    
    
    function _logReceipt(string memory _key, uint32 index, uint32 jobID, address recipient, uint received, uint returned, bytes32 resultIpfsHash, uint32[] memory dataTransfer) internal
	
    {
	emit LogReceipt(msg.sender, _key, index, jobID, recipient, 0, received, now, resultIpfsHash, dataTransfer[0], dataTransfer[1]);
    }
    
    function _logJobEvent(address _addr, string memory _key, uint32 index, bytes32[] memory sourceCodeHash, uint8[] memory storageID_cacheType) internal
    {
	emit LogJob(_addr, _key, index, storageID_cacheType[0], sourceCodeHash, storageID_cacheType[1], msg.value);
    }

    /* --------------------------------------------GETTERS-------------------------------------------- */
    
    /**
     * @dev Returns the owner of the eBlocBroker contract
     */ 
    function getOwner() external view
	returns (address) {
	return owner;
    }

    /* Returns the enrolled user's
       block number of the enrolled user, which points to the block that logs \textit{LogUser} event.
       It takes Ethereum address of the user (requester), which can be obtained by calling LogUser event.
    */
    function getUserInfo(address requester) public view
	returns (uint, string memory)
    {
	if (user[requester].committedBlock > 0)
	    return (user[requester].committedBlock, user[requester].orcID);
    }
    
    /* Returns the registered cluster's information. It takes
       Ethereum address of the cluster (clusterAddress), which can be obtained by calling getClusterAddresses
    */    
    function getClusterInfo(address clusterAddress) external view
	returns(uint32[7] memory)
    {	
	uint32[]  memory clusterInfo = pricesSetBlockNum[clusterAddress];
	uint32[7] memory clusterPriceInfo;
	    
	uint32 _pricesSetBlockNum = clusterInfo[clusterInfo.length - 1];
        if (_pricesSetBlockNum > block.number)
            _pricesSetBlockNum = clusterInfo[clusterInfo.length - 2]; // Obtain the committed prices before the block number
	
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
	returns (Lib.JobStateCodes, uint32, uint val, uint, uint, address, uint, uint)
    {
	val = cluster[clusterAddress].jobStatus[_key].length;
        if (val == 0 || val <= index)
	    return (Lib.JobStateCodes.SUBMITTED, 0, 0, 0, 0, address(0x0), 0, 0);
		
	Lib.Status storage jobInfo = cluster[clusterAddress].jobStatus[_key][index];
		
	return (jobInfo.jobs[jobID].jobStateCode,
		jobInfo.jobs[jobID].core,
		jobInfo.jobs[jobID].startTime,
		jobInfo.received,
		jobInfo.jobs[jobID].executionTimeMin,
		jobInfo.jobOwner,
		jobInfo.dataTransferIn,
		jobInfo.dataTransferOut);
    }
    
    function getClusterPricesForJob(address clusterAddress, string memory _key, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.Status      memory jobInfo     = cluster[clusterAddress].jobStatus[_key][index];
	Lib.ClusterInfo memory clusterInfo = cluster[clusterAddress].info[jobInfo.pricesSetBlockNum];
	    
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
    function getClusterAddresses() external view
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
    function isClusterExists(address clusterAddress) external view
	returns (bool)
    {
	return cluster[clusterAddress].committedBlock > 0;
    }

    /* Checks whether or not the enrolled user's given ORCID iD is already authenticated in eBlocBroker */
    function isUserOrcIDVerified(address requester) external view
	returns (bool)
    {
	return bytes(user[requester].orcID).length > 0;
    }

    /* Checks whether or not the given Ethereum address of the user (requester) 
       is already registered in eBlocBroker. 
    */
    function isUserExists(address requester) public view
	returns (bool)
    {
	return user[requester].committedBlock > 0;
    }
        
    function getReceiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) whenClusterRegistered external view
	returns (uint) {
	return cluster[msg.sender].storagedData[jobOwner][sourceCodeHash].received;
    }

    /**
     *@dev Get contract balance 
     */	   
    function getContractBalance() external view
	returns (uint)
    {
	return address(this).balance;
    }

    // Used for tests
    function getClusterSetBlockNumbers(address _addr) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[_addr];
    }

    // Used for tests 
    function getClusterReceiptSize(address clusterAddress) external view
	returns (uint32)
    {
	return cluster[clusterAddress].receiptList.getReceiptListSize();
    }

    // Used for tests 
    function getClusterReceiptNode(address clusterAddress, uint32 index) external view
	returns (uint256, int32)
    {
	return cluster[clusterAddress].receiptList.printIndex(index);
    }

}
