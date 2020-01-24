/*
  file:   eBlocBroker.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

import "./Lib.sol";
import "./SafeMath.sol";
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
    using Lib for Lib.CloudStorageID;
    using Lib for Lib.ProviderInfo;
    using Lib for Lib.JobArgument;
    using Lib for Lib.JobIndexes;

    mapping(address => uint) public balances;

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
    function transferOwnership(address newOwner)
        public
        onlyOwner
    {
        require(newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
    /**
     * @notice
     */
    function withdraw() public { // Using the withdrawal pattern
        uint256 amount = balances[msg.sender];
        // Set zero the balance before sending to prevent reentrancy attacks
        delete balances[msg.sender]; // gas refund is made
        (bool success, ) = msg.sender.call.value(amount)(""); // This forwards all available gas
        require(success, "Transfer failed."); // Return value is checked
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
    function refund(
        address _provider,
        string memory key,
        uint32 index,
        uint32 jobID,
        uint[] memory core,
        uint[] memory executionDuration
    )
        public
        returns (bool)
    {
        Lib.Provider storage provider = providers[_provider];
        /*
          If 'provider' is not mapped on 'provider' array  or its 'key' and 'index'
          is not mapped to a job , this will throw automatically and revert all changes
        */
        Lib.Status storage jobInfo = provider.jobStatus[key][index];
        require(jobInfo.jobInfo == keccak256(abi.encodePacked(core, executionDuration)));

        Lib.Job storage job = jobInfo.jobs[jobID];

        require((msg.sender == jobInfo.jobOwner || msg.sender == _provider) &&
            job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
            job.jobStateCode != Lib.JobStateCodes.REFUNDED &&
            job.jobStateCode != Lib.JobStateCodes.CANCELLED
        );

        uint256 amount;
        if (!provider.isRunning                           || // If provider stop running
            job.jobStateCode <= Lib.JobStateCodes.PENDING || // If job' state is SUBMITTED(0) or PENDING(1)
            (job.jobStateCode == Lib.JobStateCodes.RUNNING && (block.timestamp - job.startTime) > executionDuration[jobID] * 60 + 1 hours)) { // job.jobStateCode remain in running state after one hour that job should have finished
                job.jobStateCode = Lib.JobStateCodes.REFUNDED; /* Prevents double spending and re-entrancy attack */
                amount = jobInfo.received;
                jobInfo.received = 0; // Balance is zeroed out before the transfer
                balances[jobInfo.jobOwner] += amount;
        }
        else if (job.jobStateCode == Lib.JobStateCodes.RUNNING)
            job.jobStateCode = Lib.JobStateCodes.CANCELLED;
        else
            revert();

        emit LogRefundRequest(_provider, key, index, jobID, amount); /* scancel log */
        return true;
    }

    /*
    function requestDataTransferOutDeposit(
        string memory key,
        uint32 index
    )
        public
        whenProviderRunning
    {
        Lib.Provider storage provider = providers[msg.sender];
        Lib.Status   storage jobInfo  = provider.jobStatus[key][index];

        require(job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
                job.jobStateCode != Lib.JobStateCodes.REFUNDED &&
                job.jobStateCode != Lib.JobStateCodes.COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT
                );

        job.jobStateCode = Lib.JobStateCodes.COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT;
        // (msg.sender, key, index)

    }
    */

    /**
       @notice
       * Following function is a general-purpose mechanism for performing payment withdrawal
       * by the provider provider and paying of unused core, cache, and dataTransfer usage cost
       * back to the client
       * @param key  | Uniqu ID for the given job.
       * @param args | The index of the job and ID of the job to identify for workflow {index, jobID, endTime}.
       * @param executionDuration | Execution time in minutes of the completed job.
       * @param resultIpfsHash | Ipfs hash of the generated output files.
       */
    function processPayment(
        string memory key,
        Lib.JobIndexes memory args,
        uint32 executionDuration,
        bytes32 resultIpfsHash
    )
        public
        whenProviderRunning
   {
        require(args.endTime <= block.timestamp, "Ahead now");

        /* If "msg.sender" is not mapped on 'provider' struct or its "key" and "index"
           is not mapped to a job, this will throw automatically and revert all changes */
        Lib.Provider storage provider = providers[msg.sender];
        Lib.Status storage jobInfo = provider.jobStatus[key][args.index];
        require(jobInfo.jobInfo == keccak256(abi.encodePacked(args.core, args.executionDuration)));

        Lib.Job storage job = jobInfo.jobs[args.jobID]; /* Used as a pointer to a storage */

        require(job.jobStateCode != Lib.JobStateCodes.COMPLETED &&
                job.jobStateCode != Lib.JobStateCodes.REFUNDED  &&
                executionDuration <= args.executionDuration[args.jobID] && // Provider cannot request more execution time of the job that is already requested
                (args.dataTransferIn <= jobInfo.dataTransferIn || args.dataTransferOut <= jobInfo.dataTransferOut) && // Provider cannot request more than the job's given dataTransferIn or dataTransferOut
                (executionDuration > 0 && job.jobStateCode == Lib.JobStateCodes.RUNNING) // Job should be in running state if positive execution duration is provided
                );

        Lib.ProviderInfo memory info = provider.info[jobInfo.pricesSetBlockNum];

        uint amountToGain;
        uint amountToRefund;
        uint core = args.core[args.jobID];
        uint _executionDuration = args.executionDuration[args.jobID];

        if (args.dataTransferIn > 0) { // if dataTransfer[0] contains a positive value, then its the first submitted job
            if (jobInfo.cacheCost > 0) { // Checking data transferring cost
                amountToGain   = info.priceCache.mul(args.dataTransferIn);                            //cacheCostToReceive
                amountToRefund = info.priceCache.mul(jobInfo.dataTransferIn.sub(args.dataTransferIn)); //cacheCostToRefund
                require(amountToGain.add(amountToRefund) <= jobInfo.cacheCost);
                delete jobInfo.cacheCost; // Prevents additional cacheCost to be requested, can request cache cost only one time
            }

            if (jobInfo.dataTransferIn > 0 && args.dataTransferIn != jobInfo.dataTransferIn) { // Checking data transferring cost
                amountToRefund = amountToRefund.add(info.priceDataTransfer.mul((jobInfo.dataTransferIn.sub(args.dataTransferIn)))); // dataTransferRefund
                delete jobInfo.dataTransferIn; // Prevents additional cacheCost to be requested
            }
        }

        if (jobInfo.dataTransferOut > 0 && args.endJob == true && args.dataTransferOut != jobInfo.dataTransferOut) {
            amountToRefund = amountToRefund.add(info.priceDataTransfer.mul(jobInfo.dataTransferOut.sub(args.dataTransferOut)));
            delete jobInfo.dataTransferOut; // Prevents additional dataTransfer to be request for dataTransferOut
        }

                                        //computationalCost_____________________________________      //dataTransferCost_______________________________________________________
        amountToGain = amountToGain.add(uint(info.priceCoreMin).mul(core.mul(executionDuration)).add(info.priceDataTransfer.mul((args.dataTransferIn.add(args.dataTransferOut)))));

        // computationalCostRefund
        amountToRefund = amountToRefund.add(uint(info.priceCoreMin).mul(core.mul((_executionDuration.sub(uint(executionDuration))))));

        require(amountToGain.add(amountToRefund) <= jobInfo.received);

        bool success;

        if (!provider.receiptList.checkIfOverlapExists(job, uint32(args.endTime), int32(info.availableCore), core)) {
            job.jobStateCode = Lib.JobStateCodes.REFUNDED; // Important to check already refunded job or not, prevents double spending
            amountToRefund = jobInfo.received;
            jobInfo.received = 0;
            balances[jobInfo.jobOwner] += amountToRefund; // Pay back newOwned(jobInfo.received) back to the requester, which is full refund
            _logProcessPayment(key, args, resultIpfsHash, jobInfo.jobOwner, 0, amountToRefund);
            return;
        }

        if (job.jobStateCode == Lib.JobStateCodes.CANCELLED)
            job.jobStateCode = Lib.JobStateCodes.REFUNDED;  // Prevents double spending used as a Reentrancy Guard
        else
            job.jobStateCode = Lib.JobStateCodes.COMPLETED; // Prevents double spending used as a Reentrancy Guard

        jobInfo.received = jobInfo.received.sub(amountToGain.add(amountToRefund));

        if (amountToRefund > 0)
            balances[jobInfo.jobOwner] += amountToRefund; // Unused core and bandwidth is refunded back to the client

        balances[msg.sender] += amountToGain;   // Gained amount is transferred to the provider

        _logProcessPayment(key, args, resultIpfsHash, jobInfo.jobOwner, amountToGain, amountToRefund);
        return;
    }

    function refundStorageDeposit(
        address _provider,
        address payable requester,
        bytes32 sourceCodeHash
    )
        public
        returns (bool)
    {
        Lib.Provider storage provider    = providers[_provider];
        Lib.Storage  storage storageInfo = provider.storageInfo[requester][sourceCodeHash];

        uint payment = storageInfo.received;
        storageInfo.received = 0;

        require(payment > 0 && !provider.jobSt[sourceCodeHash].isVerified_Used);

        Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash];
        require(jobSt.receivedBlock.add(jobSt.storageDuration) < block.number); // Required remaining time to cache should be 0

        _cleanJobStorageTime(jobSt);
        balances[requester] += payment;
        emit LogStorageDeposit(requester, payment);

        return true;
    }

    function receiveStorageDeposit(address dataOwner, bytes32 sourceCodeHash)
        public
        whenProviderRunning
        returns (bool)
    {
        Lib.Provider       storage provider    = providers[msg.sender];
        Lib.Storage        storage storageInfo = provider.storageInfo[dataOwner][sourceCodeHash];
        Lib.JobStorageTime storage jobSt       = provider.jobSt[sourceCodeHash];

        require(jobSt.isVerified_Used && jobSt.receivedBlock.add(jobSt.storageDuration) < block.number);

        uint payment = storageInfo.received;
        storageInfo.received = 0;
        balances[msg.sender] += payment;
        _cleanJobStorageTime(jobSt);

        emit LogStorageDeposit(msg.sender, payment);
        return true;
    }

    /**
     * @notice Registers a provider's (msg.sender's) given information
     * @param email | is a string containing an email
     * @param federatedCloudID | is a string containing a Federated Cloud ID for sharing requester's repository with the provider through EUDAT.
     * @param miniLockID | is a string containing a MiniLock ID that is used by MiniLock to encrypt or decrypt files.
     * @param availableCore | is a uint32 value containing the number of available cores.
     * @param prices | is a structure containing four uint32 values, which are
     *                 fee per minute of core usage,
     *                 fee per megabyte of transferring data,
     *                 fee per megabyte of storage usage for an hour, and
     *                 fee per megabyte of cache usage values respectively.
     * @param commitmentBlockDuration | is a uint32 value containing the duration of the committed prices.
     * @param ipfsID | is a string containing an IPFS peer ID for creating peer connection between requester and provider.
     * @param whisperID | is a string containing public key for a key pair ID that is generated on Whisper.
     * @return bool
     */
    function registerProvider(
        string memory email,
        string memory federatedCloudID,
        string memory miniLockID,
        uint32 availableCore,
        uint32[] memory prices,
        uint32 commitmentBlockDuration,
        string memory ipfsID,
        string memory whisperID
    )
        public
        whenProviderNotRegistered
        returns (bool)
    {
        Lib.Provider storage provider = providers[msg.sender];

        require(availableCore > 0 && prices[0] > 0 &&
                prices[2] > 0 && // fee per storage should be minimum 1, which helps to identify is user used or not the related data file
                !provider.isRunning &&
                commitmentBlockDuration >= ONE_HOUR_BLOCK_DURATION // Commitment duration should be one day
                );

        _setProviderPrices(provider, block.number, availableCore, prices, commitmentBlockDuration);
        pricesSetBlockNum[msg.sender].push(uint32(block.number));
        provider.constructProvider();
        registeredProviders.push(msg.sender);

        emit LogProviderInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsID, whisperID);
        return true;
    }

    function updateProviderInfo(
        string memory email,
        string memory federatedCloudID,
        string memory miniLockID,
        string memory ipfsID,
        string memory whisperID
    )
        public
        whenProviderRegistered
        returns (bool)
    {
        emit LogProviderInfo(msg.sender, email, federatedCloudID, miniLockID, ipfsID, whisperID);
        return true;
    }

    /**
     * @notice Update prices and available core number of the provider
     * @param availableCore | Available core number.
     * @param commitmentBlockDuration | Requred block number duration for prices to committed.
     * @param prices | Array of prices ([priceCoreMin, priceDataTransfer, priceStorage, priceCache])
     *                 to update for the provider.
     * @return bool
     */
    function updateProviderPrices(
          uint32 availableCore,
          uint32 commitmentBlockDuration,
          uint32[] memory prices
    )
        public
        whenProviderRegistered
        returns (bool)
    {
        require(
            availableCore > 0 &&
            prices[0] > 0     &&
            commitmentBlockDuration >= ONE_HOUR_BLOCK_DURATION // Commitment duration should be one day
        );

        Lib.Provider storage provider = providers[msg.sender];

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
     * @notice Pauses provider as it will not receive any more job, which may only be performed only by the provider owner.
     */
    function pauseProvider() /* Pauses the access to the provider. Only provider owner could stop it */
        public
        whenProviderRunning
        returns (bool)
    {
        providers[msg.sender].isRunning = false; /* Provider will not accept any jobs */
        return true;
    }

    /**
     * @notice Unpauses provider as it will continue to receive jobs, which may only be performed only by the provider owner.
     */
    function unpauseProvider()
        public
        whenProviderRegistered
        whenProviderPaused
        returns (bool)
    {
        providers[msg.sender].isRunning = true; /* Provider will start accept jobs */
        return true;
    }

    /**
     * @notice Registers and updates a requester's (msg.sender's) information to eBlocBroker.
     * @param email | is a string containing an email
     * @param federatedCloudID | is a string containing a Federated Cloud ID for sharing requester's repository with the provider through EUDAT.
     * @param miniLockID | is a string containing a MiniLock ID that is used by MiniLock to encrypt or decrypt files.
     * @param ipfsID | is a string containing an IPFS peer ID for creating peer connection between requester and provider.
     * @param whisperID | is a string containing public key for a key pair ID that is generated on Whisper.
     * @return bool
     */
    function registerRequester(
        string memory email,
        string memory federatedCloudID,
        string memory miniLockID,
        string memory ipfsID,
        string memory githubName,
        string memory whisperID
    )
        public
        returns (bool)
    {
        requesterCommittedBlock[msg.sender] = uint32(block.number);
        emit LogRequester(msg.sender, email, federatedCloudID, miniLockID, ipfsID, githubName, whisperID);
        return true;
    }

    /**
       @notice
       * Registers a given data's sourceCodeHash registiration by the cluster
       * @param sourceCodeHash | Source code hashe of the provided data
       * @param price          | Price in wei of the data
       * @param commitmentBlockDuration | Commitment duration of the given price in block length
       */
    function registerData(
        bytes32 sourceCodeHash,
        uint32 price,
        uint32 commitmentBlockDuration
    )
        public
        whenProviderRegistered
    {
        Lib.RegisteredData storage registeredData = providers[msg.sender].registeredData[sourceCodeHash];

        require(
            registeredData.committedBlock.length == 0 && // In order to register, is shouldn't be already registered
            commitmentBlockDuration >= ONE_HOUR_BLOCK_DURATION
        );

        /* Always increment price of the data by 1 before storing it. By default if price == 0, data does not exist.
           If price == 1, it's an existing data that costs nothing. If price > 1, it's an existing data that costs give price. */
        if (price == 0)
            price = price + 1;

        registeredData.dataInfo[block.number].price = price;
        registeredData.dataInfo[block.number].commitmentBlockDuration = commitmentBlockDuration;
        registeredData.committedBlock.push(uint32(block.number));
        emit LogRegisterData(msg.sender, sourceCodeHash);
    }

    /**
       @notice
       * Registers a given data's sourceCodeHash removal by the cluster
       * @param sourceCodeHash | Source code hashe of the already registered data
       */
    function removeRegisteredData(bytes32 sourceCodeHash)
        public
        whenProviderRegistered
    {
        delete providers[msg.sender].registeredData[sourceCodeHash];
    }

    /**
       @notice
       * Updated a given data's sourceCodeHash registiration by the cluster
       * @param sourceCodeHash | Source code hashe of the provided data
       * @param price          | Price in wei of the data
       * @param commitmentBlockDuration | Commitment duration of the given price in block length
       */
    function updataDataPrice(
        bytes32 sourceCodeHash,
        uint32 price,
        uint32 commitmentBlockDuration
    )
        public
        whenProviderRegistered
    {
        Lib.RegisteredData storage registeredData = providers[msg.sender].registeredData[sourceCodeHash];
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
       * Performs a job submission through eBlocBroker by a requester.
       * This deposit is locked until the job is finalized or cancelled.
       * @param key is a string containing a unique name for the requester’s job.
       * @param dataTransferIn is an array of uint32 values that denote the amount of data transfer to be made in megabytes
       *                       in order to download the requester’s data from cloud storage into provider’s local storage.
       * @param dataTransferOut is a uint32 value denoting the amount of data transfer required in megabytes to upload output ﬁles generated by the requester’s job into cloud storage.
       * @param args is a structure containing additional values as follows:
       * > provider | is an Ethereum address value containing the Ethereum address of the provider that is requested to run the job.
       * > cloudStorageID | is an array of uint8 values that denote whether the requester’s data is stored and shared using either IPFS, EUDAT, IPFS (with MiniLock encryption), or Google Drive.
       * > cacheType | is an array of uint8 values that denote whether the requester’s data will be cached privately within job owner's home directory,
       *               or publicly for other requesters' access within a shared directory for all the requesters.
       * > core | is an array of uint16 values containing the number of cores requested to run the workflow with respect to each of the corresponding job.
       * > executionDuration | is an array of uint32 values containing the expected duration in minutes to run the workflow with respect to each of the corresponding job.
       * > providerPriceBlockIndex | is a uint32 value containing the block number when the requested provider set its prices most recent.
       * > dataPricesSetBlockNum | is an array of uint32 values that denote whether the provider’s registered data will be used or not.
       *                           If it is zero, then requester’s own data will be considered, which that is cached or downloaded from the cloud storage will be considered.
       *                           Otherwise it should be the block number when the requested provider’s registered data’s price is set most recent  corresponding to each of the sourceCodeHash.
       * @param storageDuration is an array of uint32 values that denote the duration it will take in hours to cache the downloaded data of the received job.
       * @param sourceCodeHash is an array of bytes32 values that are MD5 hashes with respect to each of the corresponding source code and data files.
       */
    function submitJob(
        string memory key,
        uint32[] memory dataTransferIn,
        uint32 dataTransferOut,
        Lib.JobArgument memory args,
        uint32[] memory storageDuration,
        bytes32[] memory sourceCodeHash
    )
        public
        payable
    {
        Lib.Provider storage provider = providers[args.provider];

        require(
            provider.isRunning && // Provider must be running
            sourceCodeHash.length > 0 &&
            storageDuration.length == args.dataPricesSetBlockNum.length &&
            storageDuration.length == sourceCodeHash.length &&
            storageDuration.length == dataTransferIn.length &&
            storageDuration.length == args.cloudStorageID.length &&
            storageDuration.length == args.cacheType.length &&
            args.cloudStorageID[0] <= 4 &&
            args.core.length == args.executionDuration.length &&
            doesRequesterExist(msg.sender) &&
            bytes(key).length <= 255 && // Maximum key length is 255 that will be used as folder name
            orcID[msg.sender].length > 0 &&
            orcID[args.provider].length  > 0
        );

        if (args.cloudStorageID.length > 0)
            for(uint i = 1; i < args.cloudStorageID.length; i++)
                require(args.cloudStorageID[0] == args.cloudStorageID[i] || args.cloudStorageID[i] == uint8(Lib.CloudStorageID.IPFS));

        uint32[] memory providerInfo = pricesSetBlockNum[args.provider];

        uint _providerPriceBlockIndex = providerInfo[providerInfo.length - 1];
        if (_providerPriceBlockIndex > block.number) // If the provider's price is updated on the future block
            _providerPriceBlockIndex = providerInfo[providerInfo.length - 2];

        require(args.providerPriceBlockIndex == _providerPriceBlockIndex);

        Lib.ProviderInfo memory info = provider.info[_providerPriceBlockIndex];

        uint totalCost;
        uint storageCost;

        // Here "storageDuration[0]" => block.timestamp stores the calcualted cacheCost
        // Here "dataTransferIn[0]"  => block.timestamp stores the overall dataTransferIn value, decreased if there is caching for specific block
        (totalCost, dataTransferIn[0], storageCost, storageDuration[0]) = _calculateCacheCost(provider, args, sourceCodeHash, dataTransferIn, dataTransferOut, storageDuration, info);
        totalCost = totalCost.add(_calculateComputationalCost(info, args.core, args.executionDuration));

        require(msg.value >= totalCost);

        // Here returned "_providerPriceBlockIndex" used as temp variable to hold pushed index value of the jobStatus struct
        provider.jobStatus[key].push(Lib.Status({
            cacheCost:         storageDuration[0],
            dataTransferIn:    dataTransferIn[0],
            dataTransferOut:   dataTransferOut,
            pricesSetBlockNum: uint32(_providerPriceBlockIndex),
            received:          totalCost.sub(storageCost),
            jobOwner:          msg.sender,
            sourceCodeHash:    keccak256(abi.encodePacked(sourceCodeHash, args.cacheType)),
            jobInfo:           keccak256(abi.encodePacked(args.core, args.executionDuration))}
        ));

        _providerPriceBlockIndex = provider.jobStatus[key].length - 1;

        uint refunded;
        if (msg.value != totalCost) {
            refunded = msg.value - totalCost;
            balances[msg.sender] += refunded; // Transfers extra payment (msg.value - sum), if any, back to requester (msg.sender)
        }

        _logJobEvent(key, uint32(_providerPriceBlockIndex), sourceCodeHash, args, refunded);
        return;

    }

    /**
     * @dev Logs an event for the description of the submitted job.
     * @param provider | The address of the provider.
     * @param key      | The string of the key.
     * @param desc     | The string of the description of the job.
     */
    function setJobDescription(address provider, string memory key, string memory desc)
        public
        returns (bool)
    {
        require(msg.sender == providers[provider].jobStatus[key][0].jobOwner);

        emit LogJobDescription(provider, msg.sender, key, desc);
        return true;
    }

    function sourceCodeHashReceived(
        string memory key,
        uint32 index,
        bytes32[] memory sourceCodeHash,
        uint8[] memory cacheType,
        bool[] memory isVerified
    )
        public
    {

        Lib.Provider storage provider = providers[msg.sender];
        Lib.Status memory  jobInfo = provider.jobStatus[key][index];

        require(isVerified.length == sourceCodeHash.length &&
                // List of provide sourceCodeHashes should be same as with the ones that are provided along with the job
                jobInfo.sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash, cacheType))
        );

        for (uint256 i = 0; i < sourceCodeHash.length; i++) {
            bytes32 _sourceCodeHash = sourceCodeHash[i];
            Lib.JobStorageTime storage jobSt = provider.jobSt[_sourceCodeHash]; //Only provider can update receied job only to itself
            if (!jobSt.isVerified_Used) // False if already verified and used
                if (_updateDataReceivedBlock(provider, _sourceCodeHash) && isVerified[i]) {
                    jobSt.isVerified_Used = true;
                    if (cacheType[i] == uint8(Lib.CacheType.PUBLIC))
                        jobSt.isPrivate = false;
                }

        }
    }

    /* Sets the job's state (stateID) which is obtained from Slurm */
    function setJobStatus(Lib.Job storage job, Lib.JobStateCodes jobStateCode)
        internal
        validJobStateCode(jobStateCode)
        returns (bool)
    {
        job.jobStateCode = jobStateCode;
        return true;
    }

    function setJobStatusPending(string memory key, uint32 index, uint32 jobID)
        public
        returns (bool)
    {
        Lib.Job storage job = providers[msg.sender].jobStatus[key][index].jobs[jobID]; /* Used as a pointer to a storage */
        require (job.jobStateCode == Lib.JobStateCodes.SUBMITTED, "Not permitted"); // job.jobStateCode should be {SUBMITTED (0)}
        job.jobStateCode = Lib.JobStateCodes.PENDING;
        emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.PENDING));
    }

    function setJobStatusRunning(
        string memory key,
        uint32 index,
        uint32 jobID,
        uint32 startTime
    )
        public
        whenBehindNow(startTime)
        returns (bool)
    {
        Lib.Job storage job = providers[msg.sender].jobStatus[key][index].jobs[jobID]; /* Used as a pointer to a storage */

        /* Provider can sets job's status as RUNNING and its startTime only one time */
        require (job.jobStateCode <= Lib.JobStateCodes.PENDING, "Not permitted"); // job.jobStateCode should be {SUBMITTED (0), PENDING(1)}
        job.startTime = startTime;
        job.jobStateCode = Lib.JobStateCodes.RUNNING;
        emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.RUNNING));
        return true;
    }

    function authenticateOrcID(address user, bytes32 orcid)
        public
        onlyOwner
        whenOrcidNotVerified(user)
        returns (bool)
    {
        orcID[user] = orcid;
        return true;
    }

    /* --------------------------------------------INTERNAL_FUNCTIONS-------------------------------------------- */
    function _setProviderPrices(
        Lib.Provider storage provider,
        uint mapBlock,
        uint32 availableCore,
        uint32[] memory prices,
        uint32 commitmentBlockDuration
    )
        internal
        returns (bool)
    {
        provider.info[mapBlock] = Lib.ProviderInfo({
            availableCore: availableCore,
            priceCoreMin: prices[0],
            priceDataTransfer: prices[1],
            priceStorage: prices[2],
            priceCache: prices[3],
            commitmentBlockDuration: commitmentBlockDuration
        });

        return true;
    }

    /**
     *@dev Updated data's received block number with block number
     *@param sourceCodeHash | Source-code hash of the requested data
     */
    function _updateDataReceivedBlock(Lib.Provider storage provider, bytes32 sourceCodeHash)
        internal
        returns (bool)
    {
        Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash]; //Only provider can update receied job only to itself
        if (jobSt.receivedBlock.add(jobSt.storageDuration) < block.number) // Required remaining time to cache should be 0
            return false;

        jobSt.receivedBlock = uint32(block.number) - 1; //Provider can only update the block.number
        return true;
    }

    function _calculateComputationalCost(
        Lib.ProviderInfo memory info,
        uint16[] memory core,
        uint16[] memory executionDuration
    )
        pure
        internal
            returns (uint sum)
    {
        uint executionDurationSum;
        for (uint256 i = 0; i < core.length; i++) {
            uint computationalCost = uint(info.priceCoreMin).mul(uint(core[i]).mul(uint(executionDuration[i])));
            executionDurationSum = executionDurationSum.add(executionDuration[i]);
            require(core[i] <= info.availableCore &&
                    computationalCost > 0         &&
                    executionDurationSum <= 1440 // Total execution time of the workflow should be shorter than a day
            );

            sum = sum.add(computationalCost);
        }
        return sum;
    }

    function _checkRegisteredData(
        uint32 dataPricesSetBlockNum,
        Lib.RegisteredData storage registeredData,
        uint32 cacheCost
    )
        internal
        returns (uint, uint32)
    {
        if (dataPricesSetBlockNum > 0) { // If true, then used cluster's registered data if exists
            if (registeredData.committedBlock.length > 0) {
                uint32[] memory dataCommittedBlocks = registeredData.committedBlock;
                uint32 _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 1];
                if (_dataPriceSetBlockNum > block.number)
                    _dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 2]; // Obtain the committed prices before the block number

                require(_dataPriceSetBlockNum == _dataPriceSetBlockNum);
                uint32 _dataPrice = registeredData.dataInfo[_dataPriceSetBlockNum].price; // Data is provided by the provider with its own price
                if (_dataPrice > 1)
                    cacheCost = cacheCost.add(_dataPrice);

                return (1, cacheCost);
            }
        }
        return (0, cacheCost);
    }

    function _calculateCacheCost(
        Lib.Provider storage provider,
        Lib.JobArgument memory args,
        bytes32[] memory sourceCodeHash,
        uint32[] memory dataTransferIn,
        uint32 dataTransferOut,
        uint32[] memory storageDuration,
        Lib.ProviderInfo memory info
    )
        internal
        returns (
            uint sum,
            uint32 _dataTransferIn,
            uint storageCost,
            uint32 cacheCost
        )
    {
        uint _temp;
        for (uint256 i = 0; i < sourceCodeHash.length; i++) {
            Lib.JobStorageTime storage jobSt = provider.jobSt[sourceCodeHash[i]];
            Lib.Storage storage storageInfo = provider.storageInfo[msg.sender][sourceCodeHash[i]];

            // _temp used for _receivedForStorage variable
            _temp = storageInfo.received;

            if (_temp > 0 && jobSt.receivedBlock + jobSt.storageDuration < block.number) {
                storageInfo.received = 0;
                address _provider = args.provider;
                balances[_provider] += _temp; // Transfer storagePayment back to provider
                _cleanJobStorageTime(jobSt);
                emit LogStorageDeposit(args.provider, _temp);
            }

            if (!(storageInfo.received > 0 || (jobSt.receivedBlock + jobSt.storageDuration >= block.number && !jobSt.isPrivate && jobSt.isVerified_Used))) {
                Lib.RegisteredData storage registeredData = provider.registeredData[sourceCodeHash[i]];

                // _temp used for returned bool value True or Falsep
                (_temp, cacheCost) = _checkRegisteredData(args.dataPricesSetBlockNum[i], registeredData, cacheCost);
                if (_temp == 0) { // If returned value of _checkRegisteredData is False move on to next condition
                    if (jobSt.receivedBlock + jobSt.storageDuration < block.number) {
                        if (storageDuration[i] > 0) {
                            jobSt.receivedBlock = uint32(block.number);
                            //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
                            jobSt.storageDuration = storageDuration[i].mul(ONE_HOUR_BLOCK_DURATION);

                            // _temp used for storageCostTemp variable
                            _temp = info.priceStorage.mul(dataTransferIn[i].mul(storageDuration[i]));
                            storageInfo.received = uint248(_temp);
                            storageCost = storageCost.add(_temp); //storageCost

                            if (args.cacheType[i] == uint8(Lib.CacheType.PRIVATE))
                                jobSt.isPrivate = true; // Set by the data owner
                        }
                        else
                            cacheCost = cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost
                    }
                    else
                        // Data~n is stored (privatley or publicly) on provider
                        if (storageInfo.received == 0 && // checks wheater the user is owner of the data file
                            jobSt.isPrivate == true
                            )
                            cacheCost = cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost

                    _dataTransferIn = _dataTransferIn.add(dataTransferIn[i]); //communication cost should be applied
                }
                else
                    // sourceCode is already cached
                    emit LogRegisteredDataRequestToUse(args.provider, sourceCodeHash[i]); // TODO: silinebilir
            }
        }

        sum = sum.add(info.priceDataTransfer.mul(_dataTransferIn.add(dataTransferOut))); // priceDataTransfer * (dataTransferIn + dataTransferOut)
        sum = sum.add(storageCost).add(cacheCost); // storageCost + cacheCost
        return (sum, _dataTransferIn, uint32(storageCost), uint32(cacheCost));
    }

    /**
     *@dev Cleaning for the storage struct storage (JobStorageTime, Storage) for its mapped sourceCodeHash
     */
    function _cleanJobStorageTime(Lib.JobStorageTime storage jobSt)
        internal
    {
        delete jobSt.receivedBlock;
        delete jobSt.storageDuration;
        delete jobSt.isPrivate;
        delete jobSt.isVerified_Used;
    }

    function _logProcessPayment(
        string memory key,
        Lib.JobIndexes memory args,
        bytes32 resultIpfsHash,
        address recipient,
        uint receivedWei,
        uint refundedWei
    )
        internal

    {
        emit LogProcessPayment(msg.sender, key, args.index, args.jobID, recipient, receivedWei, refundedWei, args.endTime, resultIpfsHash, args.dataTransferIn, args.dataTransferOut);
    }

    function _logJobEvent(string memory key, uint32 index, bytes32[] memory sourceCodeHash, Lib.JobArgument memory args, uint refunded)
        internal
    {
        emit LogJob(args.provider, key, index, args.cloudStorageID, sourceCodeHash, args.cacheType, args.core, args.executionDuration, msg.value, refunded);
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
    function getRegisteredDataBlockNumbers(address _provider, bytes32 sourceCodeHash)
        external
        view
        returns (uint32[] memory)
    {
        return providers[_provider].registeredData[sourceCodeHash].committedBlock;
    }

    // If _pricesSetBlockNum is 0, it will return the current price at the current block-number that is called
    // If mappings does not valid, then it will return (0, 0)
    function getRegisteredDataPrice(
        address provider,
        bytes32 sourceCodeHash,
        uint32 _pricesSetBlockNum
    )
        public
        view
        returns(Lib.DataInfo memory)
    {
        Lib.RegisteredData storage registeredData = providers[provider].registeredData[sourceCodeHash];
        if (_pricesSetBlockNum == 0) {
            uint32[] memory _dataPrices = registeredData.committedBlock;
            _pricesSetBlockNum = _dataPrices[_dataPrices.length - 1];
            if (_pricesSetBlockNum > block.number)
                _pricesSetBlockNum = _dataPrices[_dataPrices.length - 2]; // Obtain the committed data price before the block.number
        }

        return (registeredData.dataInfo[_pricesSetBlockNum]);
    }

    /* Returns the enrolled requester's
       block number of the enrolled requester, which points to the block that logs \textit{LogRequester} event.
       It takes Ethereum address of the requester, which can be obtained by calling LogRequester event.
    */
    function getRequesterInfo(address requester) public view
        returns (uint32, bytes32)
    {
        return (requesterCommittedBlock[requester], orcID[requester]);
    }

    /* Returns the registered provider's information. It takes
       Ethereum address of the provider, which can be obtained by calling getProviderAddresses

       If the _pricesSetBlockNum is 0, then it will return the current price at the current block-number that is called
    */
    function getProviderInfo(address _provider, uint32 _pricesSetBlockNum)
        public
        view
        returns(uint32, Lib.ProviderInfo memory)
    {
        uint32[] memory providerInfo = pricesSetBlockNum[_provider];

        if (_pricesSetBlockNum == 0) {
            _pricesSetBlockNum = providerInfo[providerInfo.length - 1];
            if (_pricesSetBlockNum > block.number)
                _pricesSetBlockNum = providerInfo[providerInfo.length - 2]; // Obtain the committed prices before the block number
        }

        return (_pricesSetBlockNum, providers[_provider].info[_pricesSetBlockNum]);
    }

    /**
     * @dev Returns various information about the submitted job such as the hash of output files generated by IPFS,
       UNIX timestamp on job's start time, received Wei value from the client etc.
     * @param provider | The address of the provider.
     * @param key      | The string of the key.

     */
    function getJobInfo(address provider, string memory key, uint32 index, uint jobID)
        public
        view
        returns (Lib.Job memory,  uint, address, uint, uint)
    {
        Lib.Status storage jobInfo = providers[provider].jobStatus[key][index];
        Lib.Job storage job = jobInfo.jobs[jobID];

        return (job, jobInfo.received, jobInfo.jobOwner, jobInfo.dataTransferIn, jobInfo.dataTransferOut);
    }

    function getProviderPricesForJob(address _provider, string memory key, uint index)
        public
        view
        returns (Lib.ProviderInfo memory)
    {
        Lib.Status memory jobInfo = providers[_provider].jobStatus[key][index];
        Lib.ProviderInfo memory providerInfo = providers[_provider].info[jobInfo.pricesSetBlockNum];

        return (providerInfo);
    }

    /* Returns a list of registered/updated provider's block number */
    function getUpdatedProviderPricesBlocks(address _provider)
        external
        view
        returns (uint32[] memory)
    {
        return pricesSetBlockNum[_provider];
    }

    function getJobSize(address _provider, string memory key)
        public
        view
        returns (uint)
    {
        require(providers[msg.sender].committedBlock > 0);

        return providers[_provider].jobStatus[key].length;
    }

    /* Returns balance of the requested address in Wei.
       It takes a provider's Ethereum address as parameter.
    */
    function balanceOf(address _address) external view
        returns (uint)
    {
        return balances[_address];
    }


    /* Returns a list of registered provider Ethereum addresses */
    function getProviders() external view
        returns (address[] memory)
    {
        return registeredProviders;
    }

    function getJobStorageTime(address _provider, bytes32 sourceCodeHash)
        external
        view
        returns(Lib.JobStorageTime memory)
    {
        Lib.Provider storage provider = providers[_provider];
        return (provider.jobSt[sourceCodeHash]);

    }

    /* Checks whether or not the given Ethereum address of the provider is already registered in eBlocBroker. */
    function doesProviderExist(address provider)
        external
        view
        returns (bool)
    {
        return providers[provider].committedBlock > 0;
    }

    /* Checks whether or not the enrolled requester's given ORCID iD is already authenticated in eBlocBroker. */
    function isOrcIDVerified(address _user)
        external
        view
        returns (bool)
    {

        if (orcID[_user] == "")
            return false;

        return true;
    }

    /* Checks whether or not the given Ethereum address of the requester
       is already registered in eBlocBroker.
    */
    function doesRequesterExist(address requester)
        public
        view
        returns (bool)
    {
        return requesterCommittedBlock[requester] > 0;
    }

    function getReceivedStorageDeposit(address _provider, address requester, bytes32 sourceCodeHash)
        external
        view
        whenProviderRegistered
        returns (uint)
    {
        return providers[_provider].storageInfo[requester][sourceCodeHash].received;
    }

    /**
       @notice
       * Returns block numbers where provider's prices are set
       * @param _provider | The address of the provider
       */
    function getProviderSetBlockNumbers(address _provider)
        external
        view
        returns (uint32[] memory)
    {
        return pricesSetBlockNum[_provider];
    }

    // Used for tests
    function getProviderReceiptSize(address _provider)
        external
        view
        returns (uint32)
    {
        return providers[_provider].receiptList.getReceiptListSize();
    }

    // Used for tests
    function getProviderReceiptNode(address _provider, uint32 index)
        external
        view
        returns (uint, int32)
    {
        return providers[_provider].receiptList.printIndex(index);
    }

}
