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
    using Lib for Lib.Provider;
    using Lib for Lib.Requester;
    using Lib for Lib.Status; 
    using Lib for Lib.JobStateCodes;
    using Lib for Lib.ProviderInfo;

    /**
     * @notice eBlocBroker constructor
     * @dev The eBlocBroker constructor sets the original `owner` of the contract to the msg.sender.
     */
    constructor() public {
	owner = msg.sender;	
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     * @param newOwner The address to transfer ownership to.
     */
    function transferOwnership(address newOwner) public onlyOwner
    {
	require(newOwner != address(0), "New owner is the zero address");
	emit OwnershipTransferred(owner, newOwner);
	owner = newOwner;
    }

    
    /*
      function extentStorageTime(address provider, string memory sourceCodeHash, uint cacheTime) public
      returns (bool) {
      require(cacheTime > 0);
      Lib.Provider storage provider = provider[msg.sender];

      if (provider.jobSt[sourceCodeHash].receivedBlock + provider.jobSt[sourceCodeHash].cacheDuration >= block.number) {
      provider.jobSt[sourceCodeHash].cacheDuration += cacheTime * 240;
      }
      }
    */
    
    /** 
     *	@notice 
     * Refund funds the complete amount to client if requested job is still in the pending state or
     * is not completed one hour after its required time.
     * If the job is in the running state, it triggers LogRefund event on the blockchain, 
     * which will be caught by the provider in order to cancel the job. 	  
     * @param _provider | Ethereum Address of the provider.
     * @param _key  | Uniqu ID for the given job.
     * @param index | The index of the job.
     * @param jobID | ID of the job to identify under workflow.
     * @return bool 
     */    
    function refund(address _provider, string memory _key, uint32 index, uint32 jobID, bytes32[] memory sourceCodeHash) public
	returns (bool)
    {
	Lib.Provider storage provider = provider[_provider];

	/*
	  If 'provider' is not mapped on 'provider' array  or its '_key' and 'index'
	  is not mapped to a job , this will throw automatically and revert all changes 
	*/	
	Lib.Status storage jobInfo = provider.jobStatus[_key][index];
	Lib.Job    storage job     = jobInfo.jobs[jobID];
		    
	require(msg.sender == jobInfo.jobOwner                  &&
		job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
		job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
		job.jobStateCode != Lib.JobStateCodes.CANCELLED &&
		jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash))
		);
	
	uint payment;
	if (!provider.isRunning                            || // If provider stop running
  	     job.jobStateCode == Lib.JobStateCodes.PENDING || // If job have not been started running
	    (job.jobStateCode == Lib.JobStateCodes.RUNNING && (now - job.startTime) > job.executionTimeMin * 60 + 1 hours))
	    /* job.jobStateCode remain running after one hour that job should have completed */
	    {
		job.jobStateCode = Lib.JobStateCodes.REFUNDED; /* Prevents double spending and re-entrancy attack */
		payment = jobInfo.received;
		jobInfo.received = 0;
		msg.sender.transfer(payment);
	    }
	else if (job.jobStateCode == Lib.JobStateCodes.RUNNING) {
	    job.jobStateCode = Lib.JobStateCodes.CANCELLED;
	    for (uint256 i = 0; i < sourceCodeHash.length; i++)
		provider.storagedData[jobInfo.jobOwner][sourceCodeHash[i]].isUsed = true;
	}
	else
	    revert();
	
	emit LogRefundRequest(_provider, _key, index, jobID, payment); /* scancel log */
	return true;
    }

    /**
       @notice        
       * Following function is a general-purpose mechanism for performing payment withdrawal
       * by the provider provider and paying of unused core, cache, and dataTransfer usage cost 
       * back to the client
       * @param _key  | Uniqu ID for the given job.
       * @param index_jobID | The index of the job and ID of the job to identify for workflow.
       * @param executionTimeMin | Execution time in minutes of the completed job.
       * @param resultIpfsHash | Ipfs hash of the generated output files.
       * @param endTime | // End time of the executed job.
       * @param dataTransfer | dataTransfer[0] == dataTransferIn , dataTransfer[1] == dataTransferOut
       */	
    function receiptCheck(string memory _key, uint32[2] memory index_jobID, uint32 executionTimeMin, bytes32 resultIpfsHash, uint32 endTime, uint32[] memory dataTransfer, bytes32[] memory sourceCodeHash) public whenProviderRunning
    {
	require(endTime <= now, "Ahead now");

	/* If "msg.sender" is not mapped on 'provider' struct or its "_key" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes 
	*/
	Lib.Provider storage provider = provider[msg.sender];
	Lib.Status   storage jobInfo  = provider.jobStatus[_key][index_jobID[0]];	
	Lib.Job      storage job      = jobInfo.jobs[index_jobID[1]]; /* Used as a pointer to a storage */			
	
	require(job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
		job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
		jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash)) && // Provide sourceCodeHashes should be same as with the ones that are provided with the job
		executionTimeMin <= job.executionTimeMin && // Provider cannot request more execution time of the job that is already requested
		dataTransfer[0].add(dataTransfer[1]) <= (jobInfo.dataTransferIn.add(jobInfo.dataTransferOut)) // Provider cannot request more than the job's given dataTransferOut amount
		);
	
	Lib.ProviderInfo memory info = provider.info[jobInfo.pricesSetBlockNum];
		
	uint amountToGain;
	uint amountToRefund;
	
	if (jobInfo.cacheCost > 0) {
	    // Provider cannot request more dataTransferIn that is already requested
	    require(dataTransfer[0] <= jobInfo.dataTransferIn); 
	    
	    amountToGain   = info.priceCache.mul(dataTransfer[0]);                            //cacheCostToReceive
	    amountToRefund = info.priceCache.mul(jobInfo.dataTransferIn.sub(dataTransfer[0])); //cacheCostToRefund

	    require(amountToGain.add(amountToRefund) <= jobInfo.cacheCost);
			    	    
	    delete jobInfo.cacheCost; // Prevents additional cacheCost to be requested, can request cache cost only one time
	}
	
	if (dataTransfer[1] > 0 && jobInfo.dataTransferOut > 0) {
	    amountToRefund = amountToRefund.add(info.priceDataTransfer.mul(jobInfo.dataTransferOut.sub(dataTransfer[1])));
	    delete jobInfo.dataTransferOut; // Prevents additional dataTransfer to be request for dataTransferOut
	}
	
	                                //computationalCost_________________________________________      //dataTransferCost_________________________________________________
	amountToGain = amountToGain.add(info.priceCoreMin.mul(uint32(job.core).mul(executionTimeMin)).add(info.priceDataTransfer.mul((dataTransfer[0].add(dataTransfer[1]))))); 
	
	// computationalCostRefund 
	amountToRefund = amountToRefund.add(uint256(info.priceCoreMin).mul(uint256(job.core).mul((uint256(job.executionTimeMin).sub(uint256(executionTimeMin))))));
	
	if (jobInfo.dataTransferIn > 0) {
	    amountToRefund = amountToRefund.add(info.priceDataTransfer.mul((jobInfo.dataTransferIn.sub(dataTransfer[0])))); // dataTransferRefund
	    delete jobInfo.dataTransferIn; // Prevents additional cacheCost to be requested
	}

	require(amountToGain + amountToRefund <= jobInfo.received);

	if (!provider.receiptList.receiptCheck(job, uint32(endTime), int32(info.availableCore))) {
	    job.jobStateCode = Lib.JobStateCodes.REFUNDED; // Important to check already refunded job or not, prevents double spending
	    jobInfo.jobOwner.transfer(jobInfo.received); // Pay back newOwned(jobInfo.received) to the client, full refund
	    _logReceipt(_key, index_jobID, jobInfo.jobOwner, 0, jobInfo.received, resultIpfsHash, dataTransfer);
	    delete jobInfo.received;
	    return;
	}
	
	if (job.jobStateCode == Lib.JobStateCodes.CANCELLED)
	    job.jobStateCode = Lib.JobStateCodes.REFUNDED;  // Prevents double spending
	else    
	    job.jobStateCode = Lib.JobStateCodes.COMPLETED; // Prevents double spending
		
	msg.sender.transfer(amountToGain); // Gained amount is transferred to the provider 
	provider.received = provider.received.add(amountToGain); 
	jobInfo.jobOwner.transfer(amountToRefund); // Unused core and bandwidth is refundedn back to the client 
	jobInfo.received = jobInfo.received.sub(amountToRefund.add(amountToGain));
	
	for (uint256 i = 0; i < sourceCodeHash.length; i++)
	    provider.storagedData[jobInfo.jobOwner][sourceCodeHash[i]].isUsed = true;
	
	_logReceipt(_key, index_jobID, jobInfo.jobOwner, amountToGain, amountToRefund, resultIpfsHash, dataTransfer);
	return;
    }

    function receiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) whenProviderRunning public	
	returns (bool)
    {
	Lib.Provider storage provider = provider[msg.sender];

	require(provider.jobSt[sourceCodeHash].receivedBlock.add(provider.jobSt[sourceCodeHash].cacheDuration) < block.number);
	
	uint payment = provider.storagedData[jobOwner][sourceCodeHash].received;
	delete provider.storagedData[jobOwner][sourceCodeHash].received;
	provider.received.add(payment);
	msg.sender.transfer(payment);
	emit LogStoragePayment(msg.sender, payment);

	return true;
    }
	
    /* Registers a clients (msg.sender's) to eBlocBroker. It also updates requester */
    function registerRequester(string memory email, string memory federatedCloudID, string memory miniLockID, string memory ipfsAddress, string memory githubName, string memory whisperPublicKey) public 
	returns (bool)
    {
	requester[msg.sender].committedBlock = uint32(block.number);
	emit LogRequester(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, githubName, whisperPublicKey);
	return true;
    }

    /* Registers a provider's (msg.sender's) provider to eBlocBroker */
    function registerProvider(string memory email, string memory federatedCloudID, string memory miniLockID, uint32 availableCore, uint32 priceCoreMin, uint32 priceDataTransfer, uint32 priceStorage, uint32 priceCache, uint32 commitmentBlockDuration, string memory ipfsAddress, string memory whisperPublicKey) public whenProviderNotRegistered
	returns (bool)
    {
	Lib.Provider storage provider = provider[msg.sender];
	
	require(availableCore > 0 &&
		priceCoreMin > 0  &&
		commitmentBlockDuration > 8 && //1440 // Commitment duration should be one minimum day
		!provider.isRunning
		);
			
	provider.info[block.number] = Lib.ProviderInfo({
	    availableCore:      availableCore,
		    priceCoreMin:       priceCoreMin,
		    priceDataTransfer:  priceDataTransfer,
		    priceStorage:       priceStorage,
		    priceCache:         priceCache,
 		    commitmentBlockDuration: commitmentBlockDuration
		    });
	
	pricesSetBlockNum[msg.sender].push(uint32(block.number));	    
	provider.constructProvider();
	providers.push(msg.sender); 

	emit LogProviderInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);	
	return true;
    }

    function updateProviderInfo(string memory email, string memory federatedCloudID, string memory miniLockID, string memory ipfsAddress, string memory whisperPublicKey) public whenProviderRegistered
	returns (bool)
    {
	emit LogProviderInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, whisperPublicKey);
	return true;
    }       

    
    function pauseProvider() public whenProviderRunning /* Pauses the access to the provider. Only provider owner could stop it */
	returns (bool)
    {
	provider[msg.sender].isRunning = false; /* Provider will not accept any more jobs */
	return true;
    }

    function unpauseProvider() public whenProviderRegistered whenProviderPaused
	returns (bool)
    {
	provider[msg.sender].isRunning = true; 
	return true;
    }

    /**
     * @notice Update prices and available core number of the provider
     * @param availableCore | Available core number.
     * @param commitmentBlockDuration | Requred block number duration for prices to committed.
     * @param prices | Array of prices ([priceCoreMin, priceDataTransfer, priceStorage, priceCache])
     *                 to update for the provider.
     * @return bool success
     */    
    function updateProviderPrices(uint32 availableCore, uint32 commitmentBlockDuration, uint32[] memory prices) public whenProviderRegistered
	returns (bool)
    {
	require(availableCore > 0 &&
		prices[0] > 0     &&
		commitmentBlockDuration > 8 //1440 // Commitment duration should be one day
		);
	
	Lib.Provider storage provider = provider[msg.sender];

	uint32[] memory providerInfo = pricesSetBlockNum[msg.sender];
	uint32 _pricesSetBlockNum = providerInfo[providerInfo.length-1];
	if (_pricesSetBlockNum > block.number) { // Enters if already updated futher away of the committed block
	    provider.info[uint32(_pricesSetBlockNum)] =
		Lib.ProviderInfo({
		    availableCore:           availableCore,
			    priceCoreMin:            prices[0],
			    priceDataTransfer:       prices[1],
			    priceStorage:            prices[2],
			    priceCache:              prices[3],
			    commitmentBlockDuration: commitmentBlockDuration
			    });	   
	}
	else {
	    uint _commitmentBlockDuration = provider.info[provider.committedBlock].commitmentBlockDuration;	    
	    uint committedBlockNum = _pricesSetBlockNum + _commitmentBlockDuration; //future block number

	    if (committedBlockNum <= block.number) {
		committedBlockNum = (block.number - _pricesSetBlockNum) / _commitmentBlockDuration + 1;		
		committedBlockNum = _pricesSetBlockNum + committedBlockNum * _commitmentBlockDuration;
	    }

	    provider.info[uint32(committedBlockNum)] = Lib.ProviderInfo({
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

    function registerData(bytes32 sourceCodeHash, uint price) public whenProviderRegistered
    {
	/* Always increment price of the data by 1 before storing it. By default if price == 0, data does not exist.
	   If price == 1, it's an existing data that costs nothing. If price > 1, it's an existing data that costs give price.
	*/	
	provider[msg.sender].registeredData[sourceCodeHash] = price.add(1);
    }

    /**
       @notice 
       * Performs a job submission to eBlocBroker by the client
       * @param _provider | The address of the provider
       * @param _key  | Uniqu ID for the given job
       * @param core  | Array of core for the given jobs
       * @param executionTimeMin | Array of minute to execute for the given jobs
       * @param dataTransferIn  | Array of the sizes of the give data files
       * @param dataTransferOut  | Size of the data to retrive from the generated outputs
       * @param storageID_cacheType | StorageID and cacheTupe
       * @param cacheTime | Array of times to cache the data files
       * @param sourceCodeHash | Array of source code hashes
       */
    function submitJob(address payable _provider, string memory _key, uint16[] memory core, uint16[] memory executionTimeMin, uint32[] memory dataTransferIn, uint32 dataTransferOut, uint8[] memory storageID_cacheType, uint32[] memory cacheTime, bytes32[] memory sourceCodeHash) public payable
    {
	// require(_provider != address(0), "Invalid address");

 	Lib.Provider storage provider = provider[_provider];

	require(provider.isRunning                             && // Provider must be running
		sourceCodeHash.length > 0                      &&
		cacheTime.length == sourceCodeHash.length      &&
		sourceCodeHash.length == dataTransferIn.length &&
		core.length == executionTimeMin.length &&		
		storageID_cacheType[0] <= 4   &&
		bytes(_key).length <= 255     && // Maximum _key length is 255 that will be used as folder name
		isRequesterExists(msg.sender)      &&
		bytes(requester[msg.sender].orcID).length > 0 
		);

	uint32[] memory providerInfo = pricesSetBlockNum[_provider];
	
	uint priceBlockKey;
	if (providerInfo[providerInfo.length - 1] > block.number) // If the provider's price is updated on the future block
	    priceBlockKey = providerInfo[providerInfo.length-2];
	else
	    priceBlockKey = providerInfo[providerInfo.length-1];

	Lib.ProviderInfo memory info = provider.info[priceBlockKey];
	
	uint sum;	
	uint storageCost;

	// Here "cacheTime[0]" used to store the calcualted cacheCost
	(sum, dataTransferIn[0], storageCost, cacheTime[0]) = _calculateCacheCost(_provider, provider, sourceCodeHash, dataTransferIn, dataTransferOut, cacheTime, info);	
	sum = sum.add(_calculateComputationalCost(info, core, executionTimeMin));	

	require(msg.value >= sum);

	// Here returned "priceBlockKey" used as temp variable to hold pushed index value of the jobStatus struct
	priceBlockKey = _registerJob(provider, _key, sourceCodeHash, storageCost, dataTransferIn[0], dataTransferOut, uint32(priceBlockKey), cacheTime[0]);
	
	_saveCoreAndCoreMin(provider, _key, core, executionTimeMin, priceBlockKey);
	_logJobEvent(_provider, _key, uint32(priceBlockKey), sourceCodeHash, storageID_cacheType);	
	return;
    }
    
    /**
     *@dev Updated data's received block number with block number
     *@param sourceCodeHash | Source-code hash of the requested data
     */	
    function updateDataReceivedBlock(bytes32 sourceCodeHash) public
	returns (bool)
    {
	Lib.Provider storage provider = provider[msg.sender]; //Only provider can update receied job only to itself
	if (provider.jobSt[sourceCodeHash].receivedBlock > 0)
 	    provider.jobSt[sourceCodeHash].receivedBlock = uint32(block.number); //Provider only update the block.number
	
	return true;
    }
    	
    /**
     * @dev Sets requested job's description.
     * @param _provider | The address of the provider
     * @param _key | The string of the _key
     * @param jobDesc Description of the job
     */
    function setJobDescription(address _provider, string memory _key, string memory jobDesc) public
	returns (bool)
    {
	require(msg.sender == provider[_provider].jobStatus[_key][0].jobOwner);
	
	emit LogJobDescription(_provider, _key, jobDesc);	
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(string memory _key, uint32 index, uint32 jobID, Lib.JobStateCodes jobStateCode, uint32 startTime) public
	whenBehindNow(startTime) validJobStateCode(jobStateCode) 
	returns (bool)
    {
	Lib.Job storage job = provider[msg.sender].jobStatus[_key][index].jobs[jobID]; /* Used as a pointer to a storage */

	/* Provider can sets job's status as RUNNING and its startTime only one time */
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
    
    function authenticateOrcID(address _requester, string memory orcID) onlyOwner whenOrcidNotVerified(_requester) public
	returns (bool)
    {
	requester[_requester].orcID = orcID;
	return true;
    }

    /* --------------------------------------------INTERNAL_FUNCTIONS-------------------------------------------- */

    function _registerJob(Lib.Provider storage provider, string memory _key, bytes32[] memory sourceCodeHash, uint storageCost, uint32 dataTransferIn, uint32 dataTransferOut, uint32 jobIndex, uint32 cacheCost) internal
	returns (uint)
    {
	//bytes32 _keccak256Key = keccak256(abi.encodePacked(_key));
	
	return provider.jobStatus[_key].push(Lib.Status({
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

    function _saveCoreAndCoreMin(Lib.Provider storage provider, string memory _key, uint16[] memory core, uint16[] memory executionTimeMin, uint index) internal
    {
	Lib.Status storage status = provider.jobStatus[_key][index];	
	for(uint256 i = 0; i < core.length; i++) {
	    status.jobs[i].core = core[i];    /* Requested core value for each job on the workflow*/
	    status.jobs[i].executionTimeMin = executionTimeMin[i]; 
	}
    }

    function _calculateComputationalCost(Lib.ProviderInfo memory info, uint16[] memory  core, uint16[]  memory  executionTimeMin) internal
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

    function _calculateCacheCost(address payable _provider, Lib.Provider storage provider, bytes32[] memory sourceCodeHash, uint32[] memory dataTransferIn, uint32 dataTransferOut, uint32[] memory cacheTime, Lib.ProviderInfo memory info) internal
	returns (uint sum, uint32 _dataTransferIn, uint _storageCost, uint32 _cacheCost)
    {
	for (uint256 i = 0; i < sourceCodeHash.length; i++) {
	    Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash[i]];
	    uint _receivedForStorage = provider.storagedData[msg.sender][sourceCodeHash[i]].received;

	    if (jobSt.receivedBlock + jobSt.cacheDuration < block.number) { // Remaining time to cache is 0
		_dataTransferIn = _dataTransferIn.add(dataTransferIn[i]);

		if (cacheTime[i] > 0) { // Enter if the required time in hours to cache is not 0
		    if (_receivedForStorage > 0) {
			_provider.transfer(_receivedForStorage); //storagePayment
			delete provider.storagedData[msg.sender][sourceCodeHash[i]].received;
			emit LogStoragePayment(_provider, _receivedForStorage);	    
		    }
	    
		    jobSt.receivedBlock = uint32(block.number);
		    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
		    jobSt.cacheDuration = cacheTime[i] * 240;

		    uint _storageCostTemp = info.priceStorage.mul(dataTransferIn[i].mul(cacheTime[i]));
		    provider.storagedData[msg.sender][sourceCodeHash[i]].received = uint248(_storageCostTemp);		    
		    _storageCost = _storageCost.add(_storageCostTemp);
		}
		else // Data is not cached, communication cost should be applied
		    _cacheCost = _cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost
	    }
	    else { //Data is provided by the provider with its own price
	        uint256 _dataPrice = provider.registeredData[sourceCodeHash[i]];
		if (_dataPrice > 1) 
		    _storageCost =_storageCost.add( _dataPrice);
	    }
	}
	
	sum += info.priceDataTransfer * (_dataTransferIn + dataTransferOut) + _storageCost + _cacheCost;
	return (sum, uint32(_dataTransferIn), uint32(_storageCost), uint32(_cacheCost));
    }    
    
    function _logReceipt(string memory _key, uint32[2] memory index_jobID, address recipient, uint receivedWei, uint refundedWei, bytes32 resultIpfsHash, uint32[] memory dataTransfer) internal
	
    {
	emit LogReceipt(msg.sender, _key, index_jobID[0], index_jobID[1], recipient, receivedWei, refundedWei, now, resultIpfsHash, dataTransfer[0], dataTransfer[1]);
    }
    
    function _logJobEvent(address _provider, string memory _key, uint32 index, bytes32[] memory sourceCodeHash, uint8[] memory storageID_cacheType) internal
    {
	emit LogJob(_provider, _key, index, storageID_cacheType[0], sourceCodeHash, storageID_cacheType[1], msg.value);
    }

    /* --------------------------------------------GETTERS-------------------------------------------- */

    /**
     *@dev Get contract balance 
     */	   
    function getContractBalance() external view
	returns (uint)
    {
	return address(this).balance;
    }

    /**
     * @dev Returns the owner of the eBlocBroker contract
     */ 
    function getOwner() external view
	returns (address) {
	return owner;
    }

    /* Returns the enrolled requester's
       block number of the enrolled requester, which points to the block that logs \textit{LogRequester} event.
       It takes Ethereum address of the requester, which can be obtained by calling LogRequester event.
    */
    function getRequesterInfo(address _requester) public view
	returns (uint, string memory)
    {
	Lib.Requester storage requester = requester[_requester];
	return (requester.committedBlock, requester.orcID);    	
    }
    
    /* Returns the registered provider's information. It takes
       Ethereum address of the provider, which can be obtained by calling getProviderAddresses
    */    
    function getProviderInfo(address _provider) external view
	returns(uint32[7] memory)
    {	
	uint32[]  memory providerInfo = pricesSetBlockNum[_provider];
	uint32[7] memory providerPriceInfo;
	    
	uint32 _pricesSetBlockNum = providerInfo[providerInfo.length - 1];
        if (_pricesSetBlockNum > block.number)
            _pricesSetBlockNum = providerInfo[providerInfo.length - 2]; // Obtain the committed prices before the block number
	
	Lib.ProviderInfo memory _providerPrices = provider[_provider].info[_pricesSetBlockNum];
	
	if (provider[_provider].committedBlock == 0)
	    return providerPriceInfo;

	providerPriceInfo[0] = _pricesSetBlockNum; 
	providerPriceInfo[1] = _providerPrices.availableCore;
	providerPriceInfo[2] = _providerPrices.priceCoreMin;	
	providerPriceInfo[3] = _providerPrices.priceDataTransfer;
	providerPriceInfo[4] = _providerPrices.priceStorage;
	providerPriceInfo[5] = _providerPrices.priceCache;	
	providerPriceInfo[6] = _providerPrices.commitmentBlockDuration;
	    
	return providerPriceInfo;
    }
    

    /* Returns various information about the submitted job such as the hash of output files generated by IPFS,
       UNIX timestamp on job's start time, received Wei value from the client etc. 
    */
    function getJobInfo(address _provider, string memory _key, uint32 index, uint jobID) public view
	returns (Lib.JobStateCodes, uint32, uint val, uint, uint, address, uint, uint)
    {
	val = provider[_provider].jobStatus[_key].length;
        if (val == 0 || val <= index)
	    return (Lib.JobStateCodes.SUBMITTED, 0, 0, 0, 0, address(0x0), 0, 0);
		
	Lib.Status storage jobInfo = provider[_provider].jobStatus[_key][index];
		
	return (jobInfo.jobs[jobID].jobStateCode,
		jobInfo.jobs[jobID].core,
		jobInfo.jobs[jobID].startTime,
		jobInfo.received,
		jobInfo.jobs[jobID].executionTimeMin,
		jobInfo.jobOwner,
		jobInfo.dataTransferIn,
		jobInfo.dataTransferOut);
    }
    
    function getProviderPricesForJob(address _provider, string memory _key, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.Status      memory jobInfo     = provider[_provider].jobStatus[_key][index];
	Lib.ProviderInfo memory providerInfo = provider[_provider].info[jobInfo.pricesSetBlockNum];
	    
	return (providerInfo.priceCoreMin, providerInfo.priceDataTransfer, providerInfo.priceStorage, providerInfo.priceCache);
    }

    /* Returns a list of registered/updated provider's block number */     
    function getProviderPricesBlockNumbers(address _provider) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[_provider];
    }
   
    function getJobSize(address _provider, string memory _key) public view
	returns (uint)
    {
	require(provider[msg.sender].committedBlock > 0);
	    
	return provider[_provider].jobStatus[_key].length;
    }

    /* Returns provider provider's earned money amount in Wei.
       It takes a provider's Ethereum address as parameter. 
    */
    function getProviderReceivedAmount(address _provider) external view
	returns (uint)
    {
	return provider[_provider].received;
    }
	
    /* Returns a list of registered provider Ethereum addresses */
    function getProviders() external view
	returns (address[] memory)
    {
	return providers;
    }
	
    function getJobStorageTime(address _provider, bytes32 sourceCodeHash) external view
	returns(uint, uint)
    {	    
	Lib.Provider storage provider = provider[_provider];
	
	return (provider.jobSt[sourceCodeHash].receivedBlock,
		uint256(provider.jobSt[sourceCodeHash].cacheDuration).div(240));
    }

    /* Checks whether or not the given Ethereum address of the provider 
       is already registered in eBlocBroker. 
    */
    function isProviderExists(address _provider) external view
	returns (bool)
    {
	return provider[_provider].committedBlock > 0;
    }

    /* Checks whether or not the enrolled requester's given ORCID iD is already authenticated in eBlocBroker */
    function isRequesterOrcIDVerified(address _requester) external view
	returns (bool)
    {
	return bytes(requester[_requester].orcID).length > 0;
    }

    /* Checks whether or not the given Ethereum address of the requester
       is already registered in eBlocBroker. 
    */
    function isRequesterExists(address _requester) public view
	returns (bool)
    {
	return requester[_requester].committedBlock > 0;
    }
        
    function getReceiveStoragePayment(address jobOwner, bytes32 sourceCodeHash) whenProviderRegistered external view
	returns (uint) {
	return provider[msg.sender].storagedData[jobOwner][sourceCodeHash].received;
    }

    // Used for tests
    function getProviderSetBlockNumbers(address _provider) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[_provider];
    }

    // Used for tests 
    function getProviderReceiptSize(address _provider) external view
	returns (uint32)
    {
	return provider[_provider].receiptList.getReceiptListSize();
    }

    // Used for tests 
    function getProviderReceiptNode(address _provider, uint32 index) external view
	returns (uint256, int32)
    {
	return provider[_provider].receiptList.printIndex(index);
    }

}
