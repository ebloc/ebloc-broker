/*
  file:   eBlocBroker.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
pragma experimental ABIEncoderV2;

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
    using Lib for Lib.Status; 
    using Lib for Lib.JobStateCodes;
    using Lib for Lib.StorageID;    
    using Lib for Lib.ProviderInfo;
    using Lib for Lib.JobArgument;
    using Lib for Lib.JobIndexes;
        
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
    function transferOwnership(address newOwner) public onlyOwner {
	require(newOwner != address(0), "New owner is the zero address");
	emit OwnershipTransferred(owner, newOwner);
	owner = newOwner;
    }

    /** 
     * @notice 
     * Refund funds the complete amount to client if requested job is still in the pending state or
     * is not completed one hour after its required time.
     * If the job is in the running state, it triggers LogRefund event on the blockchain, 
     * which will be caught by the provider in order to cancel the job. 	  
     * @param _provider | Ethereum Address of the provider.
     * @param key  | Uniqu ID for the given job.
     * @param index | The index of the job.
     * @param jobID | ID of the job to identify under workflow.
     * @return bool 
     */    
    function refund(address _provider, string memory key, uint32 index, uint32 jobID)
	public
	returns (bool)
    {
	Lib.Provider storage provider = provider[_provider];

	/*
	  If 'provider' is not mapped on 'provider' array  or its 'key' and 'index'
	  is not mapped to a job , this will throw automatically and revert all changes 
	*/	
	Lib.Status storage jobInfo = provider.jobStatus[key][index];
	Lib.Job    storage job     = jobInfo.jobs[jobID];
	
	require((msg.sender == jobInfo.jobOwner || msg.sender == _provider) &&
		job.jobStateCode != Lib.JobStateCodes.COMPLETED             &&
		job.jobStateCode != Lib.JobStateCodes.REFUNDED              &&
		job.jobStateCode != Lib.JobStateCodes.CANCELLED
		);
	
	uint payment;
	if (!provider.isRunning                            || // If provider stop running	    
  	     job.jobStateCode <= Lib.JobStateCodes.PENDING || // If job' state is SUBMITTED(0) or PENDING(1)
	    // job.jobStateCode remain in running state after one hour that job should have finished
	    (job.jobStateCode == Lib.JobStateCodes.RUNNING && (now - job.startTime) > job.executionTimeMin * 60 + 1 hours))	    
	    {
		job.jobStateCode = Lib.JobStateCodes.REFUNDED; /* Prevents double spending and re-entrancy attack */
		payment = jobInfo.received;
		jobInfo.received = 0;
		msg.sender.transfer(payment); // refund back to msg.sender(requester)
	    }
	else if (job.jobStateCode == Lib.JobStateCodes.RUNNING)
	    job.jobStateCode = Lib.JobStateCodes.CANCELLED;
	else
	    revert();
	
	emit LogRefundRequest(_provider, key, index, jobID, payment); /* scancel log */
	return true;
    }

    /**
       @notice        
       * Following function is a general-purpose mechanism for performing payment withdrawal
       * by the provider provider and paying of unused core, cache, and dataTransfer usage cost 
       * back to the client
       * @param key  | Uniqu ID for the given job.
       * @param args | The index of the job and ID of the job to identify for workflow {index, jobID}.
       * @param executionTimeMin | Execution time in minutes of the completed job.
       * @param resultIpfsHash | Ipfs hash of the generated output files.
       * @param endTime | // End time of the executed job.
       * @param dataTransfer | dataTransfer[0] == dataTransferIn , dataTransfer[1] == dataTransferOut.
       */	
    function processPayment(
        string memory key,
	Lib.JobIndexes memory args,
	uint32 executionTimeMin,
	bytes32 resultIpfsHash,
	uint32 endTime,
	uint32[] memory dataTransfer
    )
	public
	whenProviderRunning
    {	    
	require(endTime <= now, "Ahead now");
	    
	/* If "msg.sender" is not mapped on 'provider' struct or its "key" and "index"
	   is not mapped to a job, this will throw automatically and revert all changes */
	Lib.Provider storage provider = provider[msg.sender];
	Lib.Status   storage jobInfo  = provider.jobStatus[key][args.index];	
	Lib.Job      storage job      = jobInfo.jobs[args.jobID]; /* Used as a pointer to a storage */			

	require(job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
		job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
		executionTimeMin <= job.executionTimeMin        && // Provider cannot request more execution time of the job that is already requested
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
	amountToRefund = amountToRefund.add(uint(info.priceCoreMin).mul(uint(job.core).mul((uint(job.executionTimeMin).sub(uint(executionTimeMin))))));
	
	if (jobInfo.dataTransferIn > 0) {
	    amountToRefund = amountToRefund.add(info.priceDataTransfer.mul((jobInfo.dataTransferIn.sub(dataTransfer[0])))); // dataTransferRefund
	    delete jobInfo.dataTransferIn; // Prevents additional cacheCost to be requested
	}

	require(amountToGain + amountToRefund <= jobInfo.received);

	if (!provider.receiptList.isOverlap(job, uint32(endTime), int32(info.availableCore))) {
	    job.jobStateCode = Lib.JobStateCodes.REFUNDED; // Important to check already refunded job or not, prevents double spending
	    jobInfo.jobOwner.transfer(jobInfo.received); // Pay back newOwned(jobInfo.received) to the client, full refund
	    _logProcessPayment(key, args, jobInfo.jobOwner, 0, jobInfo.received, resultIpfsHash, dataTransfer);
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
	
	_logProcessPayment(key, args, jobInfo.jobOwner, amountToGain, amountToRefund, resultIpfsHash, dataTransfer);
	return;
    }

    function refundStorageDeposit(address _provider, address payable _requester, bytes32 sourceCodeHash)
	public
	returns (bool)
    {
	Lib.Provider storage provider    = provider[_provider];	
	Lib.Storage  storage storageInfo = provider.storageInfo[_requester][sourceCodeHash];	
	uint payment = storageInfo.received;
	require(payment > 0 && !storageInfo.isVerified_Used);

	Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash];
	require(jobSt.receivedBlock.add(jobSt.cacheDuration) < block.number); // Required remaining time to cache should be 0

	_cleanJobStorageTime_Storage(jobSt, storageInfo);	
	_requester.transfer(payment);
	emit LogStorageDeposit(_requester, payment);

	return true;
    }
    
    function receiveStorageDeposit(address dataOwner, bytes32 sourceCodeHash) whenProviderRunning
	public	
	returns (bool)
    {
	Lib.Provider       storage provider     = provider[msg.sender];
	Lib.Storage        storage storageInfo  = provider.storageInfo[dataOwner][sourceCodeHash];
	Lib.JobStorageTime storage jobSt        = provider.jobSt[sourceCodeHash];
	    	   
	require(storageInfo.isVerified_Used && jobSt.receivedBlock.add(jobSt.cacheDuration) < block.number);

	uint payment = storageInfo.received;

	_cleanJobStorageTime_Storage(jobSt, storageInfo);		
	provider.received.add(payment);
	msg.sender.transfer(payment);
	emit LogStorageDeposit(msg.sender, payment);
	    
	return true;
    }

    /**
     * @notice Registers a requester's (msg.sender's) to eBlocBroker. It also can update the requester's information.
     */
    function registerRequester(string memory email, string memory federatedCloudID, string memory miniLockID, string memory ipfsAddress, string memory githubName, string memory whisperPublicKey) public 
	returns (bool)
    {
	requesterCommittedBlock[msg.sender] = uint32(block.number);
	emit LogRequester(msg.sender, email, federatedCloudID, miniLockID, ipfsAddress, githubName, whisperPublicKey);
	return true;
    }
    
    /**
     * @notice Registers a provider's (msg.sender's) provider to eBlocBroker 
     */
    function registerProvider(string memory email, string memory federatedCloudID, string memory miniLockID, uint32 availableCore, uint32[] memory prices, uint32 commitmentBlockDuration, string memory ipfsAddress, string memory whisperPublicKey) public whenProviderNotRegistered
	returns (bool)
    {
	uint doo;
	Lib.Provider storage provider = provider[msg.sender];

	require(availableCore > 0 && prices[0] > 0 && !provider.isRunning &&
		commitmentBlockDuration > 8 //1440 // Commitment duration should be one minimum day
		);
	     
	_setProviderPrices(provider, block.number, availableCore, prices, commitmentBlockDuration);		
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
	provider[msg.sender].isRunning = false; /* Provider will not accept any jobs */
	return true;
    }

    function unpauseProvider() public whenProviderRegistered whenProviderPaused
	returns (bool)
    {
	provider[msg.sender].isRunning = true; /* Provider will start accept jobs */
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
		commitmentBlockDuration > 8 // TODO: 1440 // Commitment duration should be one day
		);
	
	Lib.Provider storage provider = provider[msg.sender];

	uint32[] memory providerInfo = pricesSetBlockNum[msg.sender];
	uint32 _pricesSetBlockNum = providerInfo[providerInfo.length - 1];
	if (_pricesSetBlockNum > block.number) // Enters if already updated futher away of the committed block on the same block
	    _setProviderPrices(provider, _pricesSetBlockNum, availableCore, prices, commitmentBlockDuration);
	else {	    
	    uint _commitmentBlockDuration = provider.info[_pricesSetBlockNum].commitmentBlockDuration;	    
	    uint _committedBlock = _pricesSetBlockNum + _commitmentBlockDuration; //future block number

	    if (_committedBlock <= block.number) {
		_committedBlock = (block.number - _pricesSetBlockNum) / _commitmentBlockDuration + 1;		
		_committedBlock = _pricesSetBlockNum + _committedBlock * _commitmentBlockDuration; // Next price cycle to be considered
	    }
	    
	    _setProviderPrices(provider, _committedBlock, availableCore, prices, commitmentBlockDuration);
	    pricesSetBlockNum[msg.sender].push(uint32(_committedBlock));
	}
	
	return true;
    }
    
    /**
       @notice 
       * Registers a given data's sourceCodeHash registiration by the cluster
       * @param sourceCodeHash | Source code hashe of the provided data
       * @param price          | Price in wei of the data
       * @param commitmentBlockDuration | Commitment duration of the given price in block length
       */
    function registerData(bytes32 sourceCodeHash, uint32 price, uint32 commitmentBlockDuration) public whenProviderRegistered
    {
	Lib.RegisteredData storage registeredData = provider[msg.sender].registeredData[sourceCodeHash];
	    
	require(registeredData.committedBlock.length == 0 && // In order to register, is shouldn't be already registered
		commitmentBlockDuration > 8 // TODO: ONE_HOUR_BLOCK_DURATION
		);
		
	/* Always increment price of the data by 1 before storing it. By default if price == 0, data does not exist.
	   If price == 1, it's an existing data that costs nothing. If price > 1, it's an existing data that costs give price. */
	if (price == 0)
	    price = price + 1;
	    
	registeredData.dataInfo[block.number].price = price;
	registeredData.dataInfo[block.number].commitmentBlockDuration = commitmentBlockDuration;
	
	registeredData.committedBlock.push(uint32(block.number));
    }
    
    /**
       @notice 
       * Registers a given data's sourceCodeHash removal by the cluster
       * @param sourceCodeHash | Source code hashe of the already registered data
       */
    function removeRegisteredData(bytes32 sourceCodeHash) public whenProviderRegistered
    {
	delete provider[msg.sender].registeredData[sourceCodeHash];
    }
	
    /**
       @notice 
       * Updated a given data's sourceCodeHash registiration by the cluster
       * @param sourceCodeHash | Source code hashe of the provided data
       * @param price          | Price in wei of the data
       * @param commitmentBlockDuration | Commitment duration of the given price in block length
       */
    function updataDataPrice(bytes32 sourceCodeHash, uint32 price, uint32 commitmentBlockDuration) public whenProviderRegistered
    {
	Lib.RegisteredData storage registeredData = provider[msg.sender].registeredData[sourceCodeHash];	
	require(registeredData.committedBlock.length > 0);
	if (price == 0)
	    price = price + 1;

	uint32[] memory committedBlockList = registeredData.committedBlock;	
	uint32 _pricesSetBlockNum = committedBlockList[committedBlockList.length - 1];

	if (_pricesSetBlockNum > block.number) { // Enters if already updated futher away of the committed block on the same block
	    registeredData.dataInfo[block.number].price = price;
	    registeredData.dataInfo[block.number].commitmentBlockDuration = commitmentBlockDuration;
	}
	else {
	    uint _commitmentBlockDuration = registeredData.dataInfo[_pricesSetBlockNum].commitmentBlockDuration;	  
	    uint _committedBlock = _pricesSetBlockNum + _commitmentBlockDuration; //future block number
	    
	    if (_committedBlock <= block.number) {
		_committedBlock = (block.number - _pricesSetBlockNum) / _commitmentBlockDuration + 1;		
		_committedBlock = _pricesSetBlockNum + _committedBlock * _commitmentBlockDuration;
	    }
	    
	    registeredData.dataInfo[_committedBlock].price = price;
	    registeredData.dataInfo[_committedBlock].commitmentBlockDuration = commitmentBlockDuration;	    
	    registeredData.committedBlock.push(uint32(_committedBlock));
	}	
    }
    
    /**
       @notice 
       * Performs a job submission to eBlocBroker by the client. Deposit Wei (given msg.value) into the eBlocBroker.
       * This deposit is locked until the job is finalized or cancelled.
       * @param _provider | The address of the provider
       * @param key  | Uniqu ID for the given job
       * @param core  | Array of core for the given jobs
       * @param executionTimeMin | Array of minute to execute for the given jobs
       * @param dataTransferIn  | Array of the sizes of the give data files
       * @param dataTransferOut  | Size of the data to retrive from the generated outputs
       * @param args | Array of storageID, cacheTupe, and prices set block number
       * @param cacheTime | Array of times to cache the data files
       * @param sourceCodeHash | Array of source code hashes
       */
    function submitJob(address payable _provider, string memory key, uint16[] memory core, uint16[] memory executionTimeMin, uint32[] memory dataTransferIn, uint32 dataTransferOut, Lib.JobArgument memory args, uint32[] memory cacheTime, bytes32[] memory sourceCodeHash) public payable
    {
 	Lib.Provider storage provider = provider[_provider];
	
	require(provider.isRunning                              && // Provider must be running
		sourceCodeHash.length > 0                       &&
		cacheTime.length == sourceCodeHash.length       &&
		sourceCodeHash.length == dataTransferIn.length  &&
		dataTransferIn.length == args.storageID.length  &&
		args.cacheType.length == dataTransferIn.length  &&
		args.dataPricesSetBlockNum.length == dataTransferIn.length  &&
		args.storageID[0] <= 4                          &&
		core.length == executionTimeMin.length          &&		
		isRequesterExists(msg.sender)                   &&
		bytes(key).length <= 255                        && // Maximum key length is 255 that will be used as folder name		
		orcID[msg.sender].length > 0                    &&
		orcID[_provider].length  > 0
		);

	if (args.storageID.length > 0) 
	    for(uint i = 1; i < args.storageID.length; i++) 
		require(args.storageID[i] == args.storageID[0] || args.storageID[i] == uint8(Lib.StorageID.IPFS));

	uint32[] memory providerInfo = pricesSetBlockNum[_provider];
	
	uint _providerPriceBlockIndex = providerInfo[providerInfo.length - 1];
	if (_providerPriceBlockIndex > block.number) // If the provider's price is updated on the future block
	    _providerPriceBlockIndex = providerInfo[providerInfo.length - 2];

	require(args.providerPriceBlockIndex == _providerPriceBlockIndex);
	
	Lib.ProviderInfo memory info = provider.info[_providerPriceBlockIndex];
	
	uint sum;
	uint storageCost;	

	// Here "cacheTime[0]"      => now stores the calcualted cacheCost
	// Here "dataTransferIn[0]" => now stores the overall dataTransferIn value, decreased if there is caching for specific block
	(sum, dataTransferIn[0], storageCost, cacheTime[0]) = _calculateCacheCost(_provider, provider, args, sourceCodeHash, dataTransferIn, dataTransferOut, cacheTime, info);	
	sum = sum.add(_calculateComputationalCost(info, core, executionTimeMin));	

	require(msg.value >= sum);

	// Here returned "_providerPriceBlockIndex" used as temp variable to hold pushed index value of the jobStatus struct
	_providerPriceBlockIndex = provider.jobStatus[key].push(Lib.Status({
		        dataTransferIn:    dataTransferIn[0],
			dataTransferOut:   dataTransferOut,
			jobOwner:          tx.origin,
			received:          msg.value - storageCost,
			pricesSetBlockNum: uint32(_providerPriceBlockIndex),
			cacheCost:         cacheTime[0], //== cacheCost
			sourceCodeHash:    keccak256(abi.encodePacked(sourceCodeHash, args.cacheType))
			}
		)) - 1;
	
	
	// __providerPriceBlockIndex = _registerJob(provider, key, storageCost, dataTransferIn[0], dataTransferOut, uint32(__providerPriceBlockIndex), cacheTime[0], keccak256(abi.encodePacked(sourceCodeHash, args.cacheType)));	
	_saveCoreAndCoreMin(provider, key, core, executionTimeMin, _providerPriceBlockIndex);
	_logJobEvent(_provider, key, uint32(_providerPriceBlockIndex), sourceCodeHash, args);	
	return;
    }
        	
    /**
     * @dev Sets requested job's description.
     * @param _provider | The address of the provider.
     * @param key      | The string of the key.
     * @param desc      | The string of the description of the job.
     */
    function setJobDescription(address _provider, string memory key, string memory desc) public
	returns (bool)
    {
	require(msg.sender == provider[_provider].jobStatus[key][0].jobOwner);
	
	emit LogJobDescription(_provider, msg.sender, key, desc);
	return true;
    }

    function sourceCodeHashReceived(string memory key, uint32 index, bytes32[] memory sourceCodeHash, uint8[] memory cacheType, bool[] memory isVerified) public
    {
	Lib.Provider storage provider = provider[msg.sender];
	Lib.Status   memory  jobInfo  = provider.jobStatus[key][index];
	
	require(isVerified.length == sourceCodeHash.length &&
		// List of provide sourceCodeHashes should be same as with the ones that are provided along with the job
		jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash, cacheType)) 
		);	
		    
	for (uint i = 0; i < sourceCodeHash.length; i++) {
	    bytes32 _sourceCodeHash = sourceCodeHash[i];
	    Lib.Storage storage storageInfo = provider.storageInfo[jobInfo.jobOwner][_sourceCodeHash];
	    if (!storageInfo.isVerified_Used) // w/in deadline
		if (_updateDataReceivedBlock(provider, _sourceCodeHash) && isVerified[i]) {		    
		    storageInfo.isVerified_Used = true;
		    if (cacheType[i] == uint8(Lib.CacheType.PUBLIC))
			provider.jobSt[_sourceCodeHash].isPrivate = false;
		}
	    
	}        
    }

    function setJobStatusPending(string memory key, uint32 index, uint32 jobID) public
	returns (bool)
    {	
	Lib.Job storage job = provider[msg.sender].jobStatus[key][index].jobs[jobID]; /* Used as a pointer to a storage */
	require (job.jobStateCode == Lib.JobStateCodes.SUBMITTED, "Not permitted"); // job.jobStateCode should be {SUBMITTED (0)}
	job.jobStateCode = Lib.JobStateCodes.PENDING;
	emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.PENDING));
    }
    
    function setJobStatusRunning(string memory key, uint32 index, uint32 jobID, uint32 startTime) public
	whenBehindNow(startTime) 
	returns (bool)
    {
	Lib.Job storage job = provider[msg.sender].jobStatus[key][index].jobs[jobID]; /* Used as a pointer to a storage */

	/* Provider can sets job's status as RUNNING and its startTime only one time */
	require (job.jobStateCode <= Lib.JobStateCodes.PENDING, "Not permitted"); // job.jobStateCode should be {SUBMITTED (0), PENDING(1)}    
	job.startTime    = startTime;
	job.jobStateCode = Lib.JobStateCodes.RUNNING;
	emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.RUNNING));
	return true;
    }
    
    function authenticateOrcID(address _user, bytes32 _orcID) onlyOwner whenOrcidNotVerified(_user) public
	returns (bool)
    {
	orcID[_user] = _orcID;
	return true;
    }

    /* --------------------------------------------INTERNAL_FUNCTIONS-------------------------------------------- */
    //    function _get(args, index)
    //internal returns (uint)
    //{
	
    //}
	    
    function _setProviderPrices(Lib.Provider storage provider, uint mapBlock, uint32 availableCore, uint32[] memory prices, uint32 commitmentBlockDuration)
	internal
	returns (bool)
    {
	provider.info[mapBlock] = Lib.ProviderInfo({
 	            availableCore:           availableCore,
		    priceCoreMin:            prices[0],
		    priceDataTransfer:       prices[1],
		    priceStorage:            prices[2],
		    priceCache:              prices[3],
		    commitmentBlockDuration: commitmentBlockDuration
		    });

	return true;
    }

    /**
     *@dev Updated data's received block number with block number
     *@param sourceCodeHash | Source-code hash of the requested data
     */	
    function _updateDataReceivedBlock(Lib.Provider storage provider, bytes32 sourceCodeHash) internal
	returns (bool)
    {
	Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash]; //Only provider can update receied job only to itself		
	if (jobSt.receivedBlock.add(jobSt.cacheDuration) < block.number) // Required remaining time to cache should be 0
	    return false;
	
	jobSt.receivedBlock = uint32(block.number) - 1; //Provider can only update the block.number	
	return true;
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(Lib.Job storage job, Lib.JobStateCodes jobStateCode) internal
	validJobStateCode(jobStateCode)
	returns (bool)
    {
	job.jobStateCode = jobStateCode;
	return true;
    }

    function _saveCoreAndCoreMin(Lib.Provider storage provider, string memory key, uint16[] memory core, uint16[] memory executionTimeMin, uint index) internal
    {
	Lib.Status storage status = provider.jobStatus[key][index];	
	for(uint i = 0; i < core.length; i++) {
	    status.jobs[i].core = core[i]; //Requested core value for each job on the workflow
	    status.jobs[i].executionTimeMin = executionTimeMin[i]; 
	}
    }

    function _calculateComputationalCost(Lib.ProviderInfo memory info, uint16[] memory  core, uint16[] memory executionTimeMin) pure internal
    	returns (uint sum)
    {
	uint executionTimeMinSum;
	for (uint i = 0; i < core.length; i++) {
	    uint computationalCost = uint(info.priceCoreMin).mul(uint(core[i]).mul(uint(executionTimeMin[i])));
	    executionTimeMinSum = executionTimeMinSum.add(executionTimeMin[i]);	    
	    require(core[i] <= info.availableCore &&
		    computationalCost > 0         &&
		    executionTimeMinSum <= 1440 // Total execution time of the workflow should be shorter than a day 
		    );
	    
	    sum = sum.add(computationalCost);
	}
	return sum;
    }

    function _doo(uint32 dataPricesSetBlockNum, Lib.RegisteredData storage registeredData, uint storageCost) internal
	returns (uint, uint)
    {
	if (dataPricesSetBlockNum > 0) { // If true, then used cluster's registered data if exists
	    if (registeredData.committedBlock.length > 0) {
		uint32[] memory dataCommittedBlocks = registeredData.committedBlock;
		uint32 _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 1];
		if (_dataPriceSetBlockNum > block.number)
		    _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 2]; // Obtain the committed prices before the block number
			
		require(_dataPriceSetBlockNum == _dataPriceSetBlockNum);
		uint _dataPrice = registeredData.dataInfo[_dataPriceSetBlockNum].price; // Data is provided by the provider with its own price
		if (_dataPrice > 1) 
		    storageCost = storageCost.add(_dataPrice);

		return (1, storageCost);
	    }
	}
	return (0, storageCost);
    }
    
    function _calculateCacheCost(address payable _provider, Lib.Provider storage provider, Lib.JobArgument memory args, bytes32[] memory sourceCodeHash, uint32[] memory dataTransferIn, uint32 dataTransferOut, uint32[] memory cacheTime, Lib.ProviderInfo memory info) internal
	returns (uint sum, uint32 _dataTransferIn, uint storageCost, uint32 _cacheCost)
    {
	uint _temp;
	for (uint i = 0; i < sourceCodeHash.length; i++) {
	    Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash[i]];	    
	    Lib.Storage storage storageInfo  = provider.storageInfo[msg.sender][sourceCodeHash[i]];

	    // _temp used for _receivedForStorage variable
	    _temp = storageInfo.received;
	    if (_temp > 0 && jobSt.receivedBlock + jobSt.cacheDuration < block.number) {
		_provider.transfer(_temp); //storagePayment
		_cleanJobStorageTime_Storage(jobSt, storageInfo);
		
		emit LogStorageDeposit(_provider, _temp);
	    }						    		    

	    if (storageInfo.received > 0 || jobSt.receivedBlock + jobSt.cacheDuration >= block.number && !jobSt.isPrivate && storageInfo.isVerified_Used)
		break;
	    else {
		Lib.RegisteredData storage registeredData = provider.registeredData[sourceCodeHash[i]];

		// _temp used for returned bool value True or False
		(_temp, storageCost) = _doo(args.dataPricesSetBlockNum[i], registeredData, storageCost);
		if (_temp == 1) {
		}
		// internal call return (args.dataPricesSetBlockNum[i]) //
		/*
		if (args.dataPricesSetBlockNum[i] > 0) { // If true, then used cluster's registered data if exists
		    if (registeredData.committedBlock.length > 0) {		    
			uint32[] memory dataCommittedBlocks = registeredData.committedBlock;		
			uint32 _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 1];
			if (_dataPriceSetBlockNum > block.number)
			    _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 2]; // Obtain the committed prices before the block number
			
			// args;
			// require(_dataPriceSetBlockNum == args.dataPricesSetBlockNum[i]); // TODO:
		    
			uint _dataPrice = registeredData.dataInfo[_dataPriceSetBlockNum].price; // Data is provided by the provider with its own price
			if (_dataPrice > 1) 
			    storageCost =storageCost.add(_dataPrice);
		    }
		}
		*/
		//
		else if (jobSt.receivedBlock + jobSt.cacheDuration < block.number) {		    		    
		    if (cacheTime[i] > 0) {
			jobSt.receivedBlock = uint32(block.number);			
			//Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
			jobSt.cacheDuration = cacheTime[i].mul(ONE_HOUR_BLOCK_DURATION);

			// _temp used for storageCostTemp variable
			_temp = info.priceStorage.mul(dataTransferIn[i].mul(cacheTime[i]));
			storageInfo.received = uint248(_temp);
			storageCost = storageCost.add(_temp); //storageCost
		
			if (args.cacheType[i] == uint8(Lib.CacheType.PRIVATE))
			    jobSt.isPrivate = true; // Set by the data owner
		    }
		    else
			_cacheCost = _cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost
		}
		else // Data is cached but privatly and storage is not requested, caching is applied
		    _cacheCost = _cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost

		_dataTransferIn = _dataTransferIn.add(dataTransferIn[i]); //communication cost should be applied		    
	    }	
	}
	
	sum = sum.add(info.priceDataTransfer.mul(_dataTransferIn.add(dataTransferOut))); // priceDataTransfer * (dataTransferIn + dataTransferOut)
	sum = sum.add(storageCost).add(_cacheCost); // storageCost + cacheCost
	return (sum, _dataTransferIn, uint32(storageCost), uint32(_cacheCost));    
    }    

    /**
     *@dev Cleaning for the storage struct storage (JobStorageTime, Storage) for its mapped sourceCodeHash
     */	   
    function _cleanJobStorageTime_Storage(Lib.JobStorageTime storage jobSt, Lib.Storage storage storageInfo) internal
    {
	delete storageInfo.received; 
	delete storageInfo.isVerified_Used;
	    
	delete jobSt.receivedBlock;
	delete jobSt.cacheDuration;
	delete jobSt.isPrivate;
    }
    
    function _logProcessPayment(string memory key, Lib.JobIndexes memory args, address recipient, uint receivedWei, uint refundedWei, bytes32 resultIpfsHash, uint32[] memory dataTransfer) internal
	
    {
	emit LogProcessPayment(msg.sender, key, args.index, args.jobID, recipient, receivedWei, refundedWei, now, resultIpfsHash, dataTransfer[0], dataTransfer[1]);
    }
    
    function _logJobEvent(address _provider, string memory key, uint32 index, bytes32[] memory sourceCodeHash, Lib.JobArgument memory args) internal
    {
	emit LogJob(_provider, key, index, args.storageID, sourceCodeHash, args.cacheType, msg.value);
    }

    /* -----------------------------------------------PUBLIC_GETTERS----------------------------------------------- */

    /**
     *@dev Get balance on eBlocBroker
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

    /* Returns a list of registered/updated provider's registered data prices */     
    function getRegisteredDataBlockNumbers(address _provider, bytes32 sourceCodeHash) external view
	returns (uint32[] memory)
    {
	return provider[_provider].registeredData[sourceCodeHash].committedBlock;
    }

    // If _pricesSetBlockNum is 0, it will return the current price at the current block-number that is called
    // If mappings does not valid, then it will return (0, 0)
    function getRegisteredDataPrice(address _provider, bytes32 sourceCodeHash, uint32 _pricesSetBlockNum) public view
	returns(uint32, uint32)
    {
	Lib.RegisteredData storage registeredData = provider[_provider].registeredData[sourceCodeHash];
	if (_pricesSetBlockNum == 0) {
	    uint32[] memory _dataPrices = registeredData.committedBlock;
	    _pricesSetBlockNum = _dataPrices[_dataPrices.length - 1];
	    if (_pricesSetBlockNum > block.number)
		_pricesSetBlockNum = _dataPrices[_dataPrices.length - 2]; // Obtain the committed data price before the block.number
	}
	
	return (registeredData.dataInfo[_pricesSetBlockNum].price, registeredData.dataInfo[_pricesSetBlockNum].commitmentBlockDuration);
    }
    
    /* Returns the enrolled requester's
       block number of the enrolled requester, which points to the block that logs \textit{LogRequester} event.
       It takes Ethereum address of the requester, which can be obtained by calling LogRequester event.
    */
    function getRequesterInfo(address _requester) public view
	returns (uint32, bytes32)
    {
	return (requesterCommittedBlock[_requester], orcID[_requester]);    	
    }
    
    /* Returns the registered provider's information. It takes
       Ethereum address of the provider, which can be obtained by calling getProviderAddresses

       If the _pricesSetBlockNum is 0, then it will return the current price at the current block-number that is called
    */    
    function getProviderInfo(address _provider, uint32 _pricesSetBlockNum) public view
	returns(uint32[7] memory)
    {	
	uint32[]  memory providerInfo = pricesSetBlockNum[_provider];
	uint32[7] memory providerPriceInfo;

	if (_pricesSetBlockNum == 0) {
	    _pricesSetBlockNum = providerInfo[providerInfo.length - 1];
	    if (_pricesSetBlockNum > block.number)
		_pricesSetBlockNum = providerInfo[providerInfo.length - 2]; // Obtain the committed prices before the block number
	}
	
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
    function getJobInfo(address _provider, string memory key, uint32 index, uint jobID) public view
	returns (Lib.JobStateCodes, uint32, uint, uint, uint, address, uint, uint)
    {
	Lib.Status storage jobInfo = provider[_provider].jobStatus[key][index];
	Lib.Job    storage job     = jobInfo.jobs[jobID];

	if (job.core == 0)
	    return (Lib.JobStateCodes.SUBMITTED, 0, 0, 0, 0, address(0x0), 0, 0);
			
	return (job.jobStateCode, job.core, job.startTime, jobInfo.received, job.executionTimeMin, jobInfo.jobOwner, jobInfo.dataTransferIn, jobInfo.dataTransferOut);
    }
	
    function getProviderPricesForJob(address _provider, string memory key, uint index) public view
	returns (uint, uint, uint, uint)
    {
	Lib.Status       memory jobInfo      = provider[_provider].jobStatus[key][index];
	Lib.ProviderInfo memory providerInfo = provider[_provider].info[jobInfo.pricesSetBlockNum];
	    
	return (providerInfo.priceCoreMin, providerInfo.priceDataTransfer, providerInfo.priceStorage, providerInfo.priceCache);
    }

    /* Returns a list of registered/updated provider's block number */     
    function getProviderPricesBlockNumbers(address _provider) external view
	returns (uint32[] memory)
    {
	return pricesSetBlockNum[_provider];
    }
   
    function getJobSize(address _provider, string memory key) public view
	returns (uint)
    {
	require(provider[msg.sender].committedBlock > 0);
	    
	return provider[_provider].jobStatus[key].length;
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
	
    function getJobStorageTime(address _provider, address _requester, bytes32 sourceCodeHash) external view
	returns(uint, uint, bool)
    {	    
	Lib.Provider storage provider = provider[_provider];
	   
	return (provider.jobSt[sourceCodeHash].receivedBlock, uint(provider.jobSt[sourceCodeHash].cacheDuration).div(ONE_HOUR_BLOCK_DURATION), provider.storageInfo[_requester][sourceCodeHash].isVerified_Used);
    }

    /* Checks whether or not the given Ethereum address of the provider is already registered in eBlocBroker. */
    function isProviderExists(address _provider) external view
	returns (bool)
    {
	return provider[_provider].committedBlock > 0;
    }

    /* Checks whether or not the enrolled requester's given ORCID iD is already authenticated in eBlocBroker. */
    function isOrcIDVerified(address _user) external view
	returns (bool)
    {
	return orcID[_user].length > 0;
    }

    /* Checks whether or not the given Ethereum address of the requester
       is already registered in eBlocBroker. 
    */
    function isRequesterExists(address _requester) public view
	returns (bool)
    {
	return requesterCommittedBlock[_requester] > 0;
    }
        
    function getReceivedStorageDeposit(address _provider, address _requester, bytes32 sourceCodeHash) whenProviderRegistered external view
	returns (uint) {
	return provider[_provider].storageInfo[_requester][sourceCodeHash].received;
    }

    /**
       @notice 
       * Returns block numbers where provider's prices are set
       * @param _provider | The address of the provider
       */
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
	returns (uint, int32)
    {
	return provider[_provider].receiptList.printIndex(index);
    }

}
