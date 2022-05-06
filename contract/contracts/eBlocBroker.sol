// SPDX-License-Identifier: MIT

/*
  file:   eBlocBroker.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity >=0.7.0 <0.9.0;
pragma experimental ABIEncoderV2;

import "./Lib.sol";
import "./SafeMath.sol";
import "./eBlocBrokerInterface.sol";
import "./EBlocBrokerBase.sol";

/**
 * @title eBlocBroker
 * @dev The eBlocBroker is a blockchain based autonomous computational resource
   broker.
 */
contract eBlocBroker is eBlocBrokerInterface, EBlocBrokerBase {
    using SafeMath32 for uint32;
    using SafeMath for uint256;
    using Lib for Lib.CloudStorageID;
    using Lib for Lib.IntervalArg;
    using Lib for Lib.JobArgument;
    using Lib for Lib.JobIndexes;
    using Lib for Lib.JobStateCodes;
    using Lib for Lib.LL;
    using Lib for Lib.Provider;
    using Lib for Lib.ProviderInfo;
    using Lib for Lib.Status;
    mapping(address => uint256) public balances;

    /**
     * @dev eBlocBroker constructor that sets the original `owner` of the
     * contract to the msg.sender.
     */
    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * It can only be called by the current owner.
     * @param newOwner The address to transfer ownership to.
     */
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "Zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @dev Withdraws the balance
     */
    function withdraw() public returns (bool) {
        // Using the withdrawal pattern
        uint256 amount = balances[msg.sender].mul(1 gwei);
        // Set zero the balance before sending to prevent reentrancy attacks
        delete balances[msg.sender]; // gas refund is made
        // Forwards all available gas
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed"); // Return value is checked
        return true;
    }

    /**
     * @dev Refund funds the complete amount to client if requested job is still
     * in the pending state or is not completed one hour after its required
     * time.  If the job is in the running state, it triggers LogRefund event on
     * the blockchain, which will be caught by the provider in order to cancel
     * the job.
     *
     * @param provider Ethereum Address of the provider.
     * @param key Uniqu ID for the given job.
     * @param index The index of the job.
     * @param jobID ID of the job to identify under workflow.
     * @return bool
     */
    function refund(
        address provider,
        string memory key,
        uint32 index,
        uint32 jobID,
        uint256[] memory core,
        uint256[] memory elapsedTime
    ) public returns (bool) {
        Lib.Provider storage _provider = providers[provider];
        /*
          If 'provider' is not mapped on '_provider' map  or its 'key' and 'index'
          is not mapped to a job , this will throw automatically and revert all changes
        */
        Lib.Status storage jobInfo = _provider.jobStatus[key][index];
        require(jobInfo.jobInfo == keccak256(abi.encodePacked(core, elapsedTime)));
        Lib.Job storage job = jobInfo.jobs[jobID];
        require(
            (msg.sender == jobInfo.jobOwner || msg.sender == provider) &&
                job.stateCode != Lib.JobStateCodes.COMPLETED &&
                job.stateCode != Lib.JobStateCodes.REFUNDED &&
                job.stateCode != Lib.JobStateCodes.CANCELLED
        );

        uint256 amount;
        if (
            !_provider.isRunning || // If provider stop running
            job.stateCode <= Lib.JobStateCodes.PENDING || // If job' state is SUBMITTED(0) or PENDING(1)
            (job.stateCode == Lib.JobStateCodes.RUNNING &&
                (block.timestamp - job.startTimestamp) > elapsedTime[jobID] * 60 + 1 hours)
        ) {
            // job.stateCode remain in running state after one hour that job should have finished
            job.stateCode = Lib.JobStateCodes.REFUNDED; /* Prevents double spending and re-entrancy attack */
            amount = jobInfo.received;
            jobInfo.received = 0; // Balance is zeroed out before the transfer
            balances[jobInfo.jobOwner] += amount;
        } else if (job.stateCode == Lib.JobStateCodes.RUNNING) {
            job.stateCode = Lib.JobStateCodes.CANCELLED;
        }
        else {
            revert();
        }
        emit LogRefundRequest(provider, key, index, jobID, amount); /* scancel log */
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

        require(job.stateCode != Lib.JobStateCodes.COMPLETED &&
                job.stateCode != Lib.JobStateCodes.REFUNDED &&
                job.stateCode != Lib.JobStateCodes.COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT
                );

        job.stateCode = Lib.JobStateCodes.COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT;
        // (msg.sender, key, index)

    }
    */

    /**
       @dev
       * Following function is a general-purpose mechanism for performing payment withdrawal
       * by the provider provider and paying of unused core, cache, and dataTransfer usage cost
       * back to the client
       * @param key Uniqu ID for the given job.
       * @param args The index of the job and ID of the job to identify for workflow {index, jobID, endTimestamp}.
       * => elapsedTime Execution time in minutes of the completed job.
       * @param resultIpfsHash Ipfs hash of the generated output files.
       */
    function processPayment(
        string memory key,
        Lib.JobIndexes memory args,
        bytes32 resultIpfsHash
    ) public whenProviderRunning {
        require(args.endTimestamp <= block.timestamp, "Ahead now");
        /* If "msg.sender" is not mapped on 'provider' struct or its "key" and "index"
           is not mapped to a job, this will throw automatically and revert all changes */
        Lib.Provider storage provider = providers[msg.sender];
        Lib.Status storage jobInfo = provider.jobStatus[key][args.index];
        require(jobInfo.jobInfo == keccak256(abi.encodePacked(args.core, args.runTime)));
        Lib.Job storage job = jobInfo.jobs[args.jobID]; /* used as a pointer to a storage */
        require(
            job.stateCode != Lib.JobStateCodes.COMPLETED &&
                job.stateCode != Lib.JobStateCodes.REFUNDED &&
                args.elapsedTime <= args.runTime[args.jobID] &&  // provider cannot request more execution time of the job that is already requested
                args.dataTransferIn <= jobInfo.dataTransferIn &&  // provider cannot request more than the job's given dataTransferIn
                args.dataTransferOut <= jobInfo.dataTransferOut &&  // provider cannot request more than the job's given dataTransferOut
                (args.elapsedTime > 0 && job.stateCode == Lib.JobStateCodes.RUNNING)  // job should be in running state if positive execution duration is provided
        );
        Lib.ProviderInfo memory info = provider.info[jobInfo.pricesSetBlockNum];
        uint256 amountToGain;
        uint256 amountToRefund;
        uint256 core = args.core[args.jobID];
        uint256 runTime = args.runTime[args.jobID];
        if (args.dataTransferIn > 0) {
            // if dataTransferIn contains a positive value, then its the first submitted job
            if (jobInfo.cacheCost > 0) {
                // Checking data transferring cost
                amountToGain = info.priceCache.mul(args.dataTransferIn); //cache_cost_to_receive
                amountToRefund = info.priceCache.mul(jobInfo.dataTransferIn.sub(args.dataTransferIn)); //cache_cost_to_refund
                require(amountToGain.add(amountToRefund) <= jobInfo.cacheCost);
                delete jobInfo.cacheCost; // Prevents additional cacheCost to be requested, can request cache cost only one time
            }
            if (jobInfo.dataTransferIn > 0 && args.dataTransferIn != jobInfo.dataTransferIn) {
                // Checking data transferring cost
                amountToRefund = amountToRefund.add( // dataTransferRefund
                    info.priceDataTransfer.mul((jobInfo.dataTransferIn.sub(args.dataTransferIn)))
                );
                // Prevents additional cacheCost to be requested
                delete jobInfo.dataTransferIn;
            }
        }

        if (jobInfo.dataTransferOut > 0 && args.endJob == true && args.dataTransferOut != jobInfo.dataTransferOut) {
            amountToRefund = amountToRefund.add(
                info.priceDataTransfer.mul(jobInfo.dataTransferOut.sub(args.dataTransferOut))
            );

            if (jobInfo.cacheCost > 0) {
                // If job cache is not used full refund for cache
                amountToRefund = amountToRefund.add(info.priceCache.mul(jobInfo.cacheCost));
                delete jobInfo.cacheCost;
            }

            if (jobInfo.dataTransferIn > 0 && args.dataTransferIn == 0) {
                // If job data transfer is not used full refund for cache
                amountToRefund = amountToRefund.add(info.priceDataTransfer.mul(jobInfo.dataTransferIn));
                delete jobInfo.dataTransferIn;
            }

            // Prevents additional dataTransfer profit to be request for dataTransferOut
            delete jobInfo.dataTransferOut;
        }
        amountToGain = amountToGain.add(
            uint256(info.priceCoreMin).mul(core.mul(args.elapsedTime)).add( // computational_cost
                info.priceDataTransfer.mul((args.dataTransferIn.add(args.dataTransferOut))) // data_transfer_cost
            )
        );
        amountToRefund = amountToRefund.add( // computational_cost_refund
            uint256(info.priceCoreMin).mul(core.mul((runTime.sub(uint256(args.elapsedTime)))))
        );
        require(amountToGain.add(amountToRefund) <= jobInfo.received);
        Lib.IntervalArg memory _interval;
        _interval.startTimestamp = job.startTimestamp;
        _interval.endTimestamp = uint32(args.endTimestamp);
        _interval.availableCore = int32(info.availableCore);
        _interval.core = int32(int256(core)); // int32(core);
        if (provider.receiptList.checkIfOverlapExists(_interval) == 0) {
            // Important to check already refunded job or not, prevents double spending
            job.stateCode = Lib.JobStateCodes.REFUNDED;
            amountToRefund = jobInfo.received;
            jobInfo.received = 0;
            // Pay back newOwned(jobInfo.received) back to the requester, which is full refund
            balances[jobInfo.jobOwner] += amountToRefund;
            _logProcessPayment(key, args, resultIpfsHash, jobInfo.jobOwner, 0, amountToRefund);
            return;
        }
        if (job.stateCode == Lib.JobStateCodes.CANCELLED) {
            // prevents double spending used as a reentrancy guard
            job.stateCode = Lib.JobStateCodes.REFUNDED;
        } else {
            // prevents double spending used as a reentrancy guard
            job.stateCode = Lib.JobStateCodes.COMPLETED;
        }
        jobInfo.received = jobInfo.received.sub(amountToGain.add(amountToRefund));
        // unused core and bandwidth is refunded back to the client
        if (amountToRefund > 0) {
            balances[jobInfo.jobOwner] += amountToRefund;
        }
        // Gained amount is transferred to the provider
        balances[msg.sender] += amountToGain;
        _logProcessPayment(key, args, resultIpfsHash, jobInfo.jobOwner, amountToGain, amountToRefund);
        return;
    }

    function refundStorageDeposit(
        address provider,
        address payable requester,
        bytes32 sourceCodeHash
    ) public returns (bool) {
        Lib.Provider storage _provider = providers[provider];
        Lib.Storage storage storageInfo = _provider.storageInfo[requester][sourceCodeHash];
        uint256 payment = storageInfo.received;
        storageInfo.received = 0;
        require(payment > 0 && !_provider.jobSt[sourceCodeHash].isVerifiedUsed);
        Lib.JobStorage storage jobSt = _provider.jobSt[sourceCodeHash];
        // Required remaining time to cache should be 0
        require(jobSt.receivedBlock.add(jobSt.storageDuration) < block.number);
        _cleanJobStorage(jobSt);
        balances[requester] += payment;
        emit LogDepositStorage(requester, payment);
        return true;
    }

    function depositStorage(address dataOwner, bytes32 sourceCodeHash) public whenProviderRunning returns (bool) {
        Lib.Provider storage provider = providers[msg.sender];
        Lib.Storage storage storageInfo = provider.storageInfo[dataOwner][sourceCodeHash];
        Lib.JobStorage storage jobSt = provider.jobSt[sourceCodeHash];
        require(jobSt.isVerifiedUsed && jobSt.receivedBlock.add(jobSt.storageDuration) < block.number);
        uint256 payment = storageInfo.received;
        storageInfo.received = 0;
        balances[msg.sender] += payment;
        _cleanJobStorage(jobSt);
        emit LogDepositStorage(msg.sender, payment);
        return true;
    }

    /**
     * @dev Registers a provider's (msg.sender's) given information
     *
     * @param gpgFingerprint is a bytes8 containing a gpg key ID that is used by GNU
       Privacy Guard to encrypt or decrypt files.
     * @param gmail is a string containing an gmail
     * @param fcID is a string containing a Federated Cloud ID for
       sharing requester's repository with the provider through EUDAT.
     * @param availableCore is a uint32 value containing the number of available
       cores.
     * @param prices is a structure containing four uint32 values, which are
     *        => fee per minute of core usage,
     *        => fee per megabyte of transferring data,
     *        => fee per megabyte of storage usage for an hour, and
     *        => fee per megabyte of cache usage values respectively.
     * @param commitmentBlockDur is a uint32 value containing the duration
       of the committed prices.
     * @param ipfsID is a string containing an IPFS peer ID for creating peer
       connection between requester and provider.
     * @return bool
     */
    function registerProvider(
        bytes32 gpgFingerprint,
        string memory gmail,
        string memory fcID,
        string memory ipfsID,
        uint32 availableCore,
        uint32[] memory prices,
        uint32 commitmentBlockDur
    ) public whenProviderNotRegistered returns (bool) {
        Lib.Provider storage provider = providers[msg.sender];
        require(
            availableCore > 0 &&
                prices[0] > 0 &&
                // fee per storage should be minimum 1, which helps to identify
                // is user used or not the related data file
                prices[2] > 0 &&
                !provider.isRunning &&
                // Commitment duration should be one day
                commitmentBlockDur >= ONE_HOUR_BLOCK_DURATION
        );

        _setProviderPrices(provider, block.number, availableCore, prices, commitmentBlockDur);
        pricesSetBlockNum[msg.sender].push(uint32(block.number));
        provider.construct();
        registeredProviders.push(msg.sender);
        emit LogProviderInfo(msg.sender, gpgFingerprint, gmail, fcID, ipfsID);
        return true;
    }

    function updateProviderInfo(
        bytes32 gpgFingerprint,
        string memory gmail,
        string memory fcID,
        string memory ipfsID
    ) public whenProviderRegistered returns (bool) {
        emit LogProviderInfo(msg.sender, gpgFingerprint, gmail, fcID, ipfsID);
        return true;
    }

    function setDataVerified(bytes32[] memory sourceCodeHash) public whenProviderRunning returns (bool){
        Lib.Provider storage provider = providers[msg.sender];
        for (uint256 i = 0; i < sourceCodeHash.length; i++) {
            bytes32 codeHash = sourceCodeHash[i];
            if (_updateDataReceivedBlock(provider, codeHash))
                provider.jobSt[codeHash].isVerifiedUsed = true;
        }
        return true;
    }

    function setDataPublic(
        string memory key,
        uint32 index,
        bytes32[] memory sourceCodeHash,
        uint8[] memory cacheType
    ) public whenProviderRunning {
        Lib.Provider storage provider = providers[msg.sender];
        // List of provide sourceCodeHash should be same as with the ones that
        // are provided along with the job
        require(provider.jobStatus[key][index].sourceCodeHash == keccak256(abi.encodePacked(sourceCodeHash, cacheType)));
        for (uint256 i = 0; i < sourceCodeHash.length; i++) {
            Lib.JobStorage storage jobSt = provider.jobSt[sourceCodeHash[i]];
            if (jobSt.isVerifiedUsed && cacheType[i] == uint8(Lib.CacheType.PUBLIC))
                jobSt.isPrivate = false;
        }
    }

    /**
     * @dev Update prices and available core number of the provider
     *
     * @param availableCore Available core number.
     * @param commitmentBlockDur Requred block number duration for prices
     * to committed.
     * @param prices Array of prices ([priceCoreMin, priceDataTransfer,
     * priceStorage, priceCache]) to update for the provider.
     * @return bool
     */
    function updateProviderPrices(
        uint32 availableCore,
        uint32 commitmentBlockDur,
        uint32[] memory prices
    ) public whenProviderRegistered returns (bool) {
        require(
            // Commitment duration should be one day
            availableCore > 0 && prices[0] > 0 && commitmentBlockDur >= ONE_HOUR_BLOCK_DURATION
        );
        Lib.Provider storage provider = providers[msg.sender];
        uint32[] memory providerInfo = pricesSetBlockNum[msg.sender];
        uint32 pricesSetBn = providerInfo[providerInfo.length - 1];
        if (pricesSetBn > block.number) {
            // Enters if already updated futher away of the committed block on the same block
            _setProviderPrices(provider, pricesSetBn, availableCore, prices, commitmentBlockDur);
        } else {
            uint256 _commitmentBlockDur = provider.info[pricesSetBn].commitmentBlockDur;
            //: future block number
            uint256 committedBlock = pricesSetBn + _commitmentBlockDur;
            if (committedBlock <= block.number) {
                committedBlock = (block.number - pricesSetBn) / _commitmentBlockDur + 1;
                // Next price cycle to be considered
                committedBlock = pricesSetBn + committedBlock * _commitmentBlockDur;
            }
            _setProviderPrices(provider, committedBlock, availableCore, prices, commitmentBlockDur);
            pricesSetBlockNum[msg.sender].push(uint32(committedBlock));
        }

        return true;
    }

    /**
     * @dev Suspends provider as it will not receive any more job, which may
     * only be performed only by the provider owner.  Suspends the access
     * to the provider. Only provider owner could stop it.
     */
    function suspendProvider() public whenProviderRunning returns (bool) {
        providers[msg.sender].isRunning = false; /* Provider will not accept any jobs */
        return true;
    }

    /**
     * @dev Resumes provider as it will continue to receive jobs, which may
     * only be performed only by the provider owner.
     */
    function resumeProvider() public whenProviderRegistered whenProviderSuspended returns (bool) {
        providers[msg.sender].isRunning = true; /* Provider will start accept jobs */
        return true;
    }

    /**
     * @dev Register or update a requester's (msg.sender's) information to
     * eBlocBroker.
     *
     * @param gpgFingerprint | is a bytes8 containing a gpg key ID that is used by the
       GNU Privacy Guard to encrypt or decrypt files.
     * @param gmail is a string containing an gmail
     * @param fcID is a string containing a Federated Cloud ID for
       sharing requester's repository with the provider through EUDAT.
     * @param ipfsID | is a string containing an IPFS peer ID for creating peer
       connection between requester and provider.
     * @return bool
     */
    function registerRequester(
        bytes32 gpgFingerprint,
        string memory gmail,
        string memory fcID,
        string memory ipfsID
    ) public returns (bool) {
        requesterCommittedBlock[msg.sender] = uint32(block.number);
        emit LogRequester(msg.sender, gpgFingerprint, gmail, fcID, ipfsID);
        return true;
    }

    /**
     * @dev Registers a given data's sourceCodeHash by the cluster
     *
     * @param sourceCodeHash source code hash of the provided data
     * @param price Price in Gwei of the data
     * @param commitmentBlockDur | Commitment duration of the given price
       in block duration
       */
    function registerData(
        bytes32 sourceCodeHash,
        uint32 price,
        uint32 commitmentBlockDur
    ) public whenProviderRegistered {
        Lib.RegisteredData storage registeredData = providers[msg.sender].registeredData[sourceCodeHash];
        require(
            registeredData.committedBlock.length == 0 && // in order to register, is shouldn't be already registered
                commitmentBlockDur >= ONE_HOUR_BLOCK_DURATION
        );

        /* Always increment price of the data by 1 before storing it. By default
           if price == 0, data does not exist.  If price == 1, it's an existing
           data that costs nothing. If price > 1, it's an existing data that
           costs give price. */
        if (price == 0) {
            price = price + 1;
        }
        registeredData.dataInfo[block.number].price = price;
        registeredData.dataInfo[block.number].commitmentBlockDur = commitmentBlockDur;
        registeredData.committedBlock.push(uint32(block.number));
        emit LogRegisterData(msg.sender, sourceCodeHash);
    }

    /**
     * @dev Registers a given data's sourceCodeHash removal by the cluster
     *
     * @param sourceCodeHash: source code hashe of the already registered data
     */
    function removeRegisteredData(bytes32 sourceCodeHash) public whenProviderRegistered {
        delete providers[msg.sender].registeredData[sourceCodeHash];
    }

    /**
     * @dev Updated a given data's prices registiration by the cluster
     *
     * @param sourceCodeHash: Source code hashe of the provided data
     * @param price: Price in Gwei of the data
     * @param commitmentBlockDur: Commitment duration of the given price
         in block duration
       */
    function updataDataPrice(
        bytes32 sourceCodeHash,
        uint32 price,
        uint32 commitmentBlockDur
    ) public whenProviderRegistered {
        Lib.RegisteredData storage registeredData = providers[msg.sender].registeredData[sourceCodeHash];
        require(registeredData.committedBlock.length > 0);
        if (price == 0) {
            price = price + 1;
        }
        uint32[] memory committedBlockList = registeredData.committedBlock;
        uint32 pricesSetBn = committedBlockList[committedBlockList.length - 1];
        if (pricesSetBn > block.number) {
            // enters if already updated futher away of the committed block on the commitment duration
            registeredData.dataInfo[pricesSetBn].price = price;
            registeredData.dataInfo[pricesSetBn].commitmentBlockDur = commitmentBlockDur;
        } else {
            uint256 _commitmentBlockDur = registeredData.dataInfo[pricesSetBn].commitmentBlockDur;
            uint256 committedBlock = pricesSetBn + _commitmentBlockDur; // future block number
            if (committedBlock <= block.number) {
                committedBlock = (block.number - pricesSetBn) / _commitmentBlockDur + 1;
                committedBlock = pricesSetBn + committedBlock * _commitmentBlockDur;
            }
            registeredData.dataInfo[committedBlock].price = price;
            registeredData.dataInfo[committedBlock].commitmentBlockDur = commitmentBlockDur;
            registeredData.committedBlock.push(uint32(committedBlock));
        }
    }

    /**
     * @dev Performs a job submission through eBlocBroker by a requester. This
       deposit is locked until the job is
     * finalized or cancelled.
     *
     * @param key Contains a unique name for the requester’s job.
     * @param dataTransferIn An array of uint32 values that denote the amount of
              data transfer to be made in megabytes in order to download the
              requester’s data from cloud storage into provider’s local storage.
     * @param args is a structure containing additional values as follows:
     * => provider is an Ethereum address value containing the Ethereum address
          of the provider that is requested to run the job.
     * => cloudStorageID | An array of uint8 values that denote whether the
          requester’s data is stored and shared using either IPFS, EUDAT, IPFS
          (with GNU Privacy Guard encryption), or Google Drive.
     * => cacheType An array of uint8 values that denote whether the requester’s
          data will be cached privately within job owner's home directory, or
          publicly for other requesters' access within a shared directory for
          all the requesters.
     * => core An array of uint16 values containing the number of cores
          requested to run the workflow with respect to each of the
          corresponding job.
     * => The runTime argument is an array of uint32 values containing the
          expected run time in minutes to run the workflow regarding each of the
          corresponding jobs.
     * => priceBlockIndex The uint32 value containing the block number
          when the requested provider set its prices most recent.
     * => dataPricfesSetBlockNum An array of uint32 values that denote whether
          the provider’s registered data will be used or not. If it is zero,
          then requester’s own data will be considered, which that is cached or
          downloaded from the cloud storage will be considered.  Otherwise it
          should be the block number when the requested provider’s registered
          data’s price is set most recent corresponding to each of the
          sourceCodeHash.
     * => dataTransferOut Value denoting the amount of data transfer required in
          megabytes to upload output files generated by the requester’s job into
          cloud storage.
     * @param storageDuration An array of uint32 values that denote the duration
              it will take in hours to cache the downloaded data of the received
              job.
     * @param sourceCodeHash An array of bytes32 values that are MD5 hashes with
              respect to each of the corresponding source code and data files.
     */
    function submitJob(
        string memory key,
        uint32[] memory dataTransferIn,
        Lib.JobArgument memory args,
        uint32[] memory storageDuration,
        bytes32[] memory sourceCodeHash
    ) public payable {
        Lib.Provider storage provider = providers[args.provider];
        require(
            provider.isRunning &&
                sourceCodeHash.length > 0 &&
                storageDuration.length == args.dataPricesSetBlockNum.length &&
                storageDuration.length == sourceCodeHash.length &&
                storageDuration.length == dataTransferIn.length &&
                storageDuration.length == args.cloudStorageID.length &&
                storageDuration.length == args.cacheType.length &&
                args.cloudStorageID[0] <= 4 &&
                args.core.length == args.runTime.length &&
                doesRequesterExist(msg.sender) &&
                bytes(key).length <= 64 &&
                orcID[msg.sender].length > 0 &&
                orcID[args.provider].length > 0
        );
        if (args.cloudStorageID.length > 0)
            for (uint256 i = 1; i < args.cloudStorageID.length; i++)
                require(
                    args.cloudStorageID[0] == args.cloudStorageID[i] ||
                    args.cloudStorageID[i] <= uint8(Lib.CloudStorageID.NONE) // IPFS or IPFS_GPG or NONE
                );

        uint32[] memory providerInfo = pricesSetBlockNum[args.provider];
        uint256 priceBlockIndex = providerInfo[providerInfo.length - 1];
        if (priceBlockIndex > block.number) {
            // if the provider's price is updated on the future block enter
            priceBlockIndex = providerInfo[providerInfo.length - 2];
        }
        require(args.priceBlockIndex == priceBlockIndex);
        Lib.ProviderInfo memory info = provider.info[priceBlockIndex];
        uint256 cost;
        uint256 storageCost;
        // "storageDuration[0]" => block.timestamp stores the calcualted cacheCost
        // "dataTransferIn[0]"  => block.timestamp stores the overall dataTransferIn value,
        //                         decreased if there is caching for specific block
        (cost, dataTransferIn[0], storageCost, storageDuration[0]) = _calculateCacheCost(
            provider,
            args,
            sourceCodeHash,
            dataTransferIn,
            storageDuration,
            info
        );
        uint msg_value = msg.value.div(1 gwei);
        cost = cost.add(_calculateComputationalCost(info, args.core, args.runTime));
        require(msg_value >= cost);
        // Here returned "priceBlockIndex" used as temp variable to hold pushed index value of the jobStatus struct
        Lib.Status storage jobInfo = provider.jobStatus[key].push();
        jobInfo.cacheCost = storageDuration[0];
        jobInfo.dataTransferIn = dataTransferIn[0];
        jobInfo.dataTransferOut = args.dataTransferOut;
        jobInfo.pricesSetBlockNum = uint32(priceBlockIndex);
        jobInfo.received = cost.sub(storageCost);
        jobInfo.jobOwner = payable(msg.sender);
        jobInfo.sourceCodeHash = keccak256(abi.encodePacked(sourceCodeHash, args.cacheType));
        jobInfo.jobInfo = keccak256(abi.encodePacked(args.core, args.runTime));
        priceBlockIndex = provider.jobStatus[key].length - 1;
        uint256 refunded;
        if (msg_value != cost) {
            refunded = (msg_value - cost);
            // transfers extra payment (msg.value - sum), if any, back to requester (msg.sender)
            balances[msg.sender] += refunded;
        }
        emitLogJob(key, uint32(priceBlockIndex), sourceCodeHash, args, refunded, msg_value);
        return;
    }

    /**
     * @dev Logs an event for the description of the submitted job.
     *
     * @param provider The address of the provider.
     * @param key The string of the key.
     * @param desc The string of the description of the job.
     */
    function setJobDescription(
        address provider,
        string memory key,
        string memory desc
    ) public returns (bool) {
        require(msg.sender == providers[provider].jobStatus[key][0].jobOwner);
        emit LogJobDescription(provider, msg.sender, key, desc);
        return true;
    }

    /* @dev Sets the job's state (stateCode) which is obtained from Slurm */
    function setJobState(Lib.Job storage job, Lib.JobStateCodes stateCode)
        internal
        validJobStateCode(stateCode)
        returns (bool)
    {
        job.stateCode = stateCode;
        return true;
    }

    /* function setJobStatePending( */
    /*     string memory key, */
    /*     uint32 index, */
    /*     uint32 jobID */
    /* ) public returns (bool) {         */
    /*     Lib.Job storage job = providers[msg.sender].jobStatus[key][index].jobs[jobID]; */
    /*     // job.stateCode should be {SUBMITTED (0)} */
    /*     require(job.stateCode == Lib.JobStateCodes.SUBMITTED, "Not permitted"); */
    /*     job.stateCode = Lib.JobStateCodes.PENDING; */
    /*     emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.PENDING)); */
    /* } */

    function setJobStateRunning(
        string memory key,
        uint32 index,
        uint32 jobID,
        uint32 startTimestamp
    ) public whenBehindNow(startTimestamp) returns (bool) {
        /* Used as a pointer to a storage */
        Lib.Job storage job = providers[msg.sender].jobStatus[key][index].jobs[jobID];
        /* Provider can sets job's status as RUNNING and its startTimestamp only one time
           job.stateCode should be {SUBMITTED (0), PENDING(1)} */
        require(job.stateCode <= Lib.JobStateCodes.PENDING, "Not permitted");
        job.startTimestamp = startTimestamp;
        job.stateCode = Lib.JobStateCodes.RUNNING;
        emit LogSetJob(msg.sender, key, index, jobID, uint8(Lib.JobStateCodes.RUNNING));
        return true;
    }

    function authenticateOrcID(address user, bytes32 orcid) public onlyOwner whenOrcidNotVerified(user) returns (bool) {
        orcID[user] = orcid;
        return true;
    }

    /* ===============================================INTERNAL_FUNCTIONS=============================================== */
    function _setProviderPrices(
        Lib.Provider storage provider,
        uint256 mapBlock,
        uint32 availableCore,
        uint32[] memory prices,
        uint32 commitmentBlockDur
    ) internal returns (bool) {
        provider.info[mapBlock] = Lib.ProviderInfo({
            availableCore: availableCore,
            priceCoreMin: prices[0],
            priceDataTransfer: prices[1],
            priceStorage: prices[2],
            priceCache: prices[3],
            commitmentBlockDur: commitmentBlockDur
        });
        return true;
    }

    /**
     * @dev Updated data's received block number with block number
     * @param provider Structure of the provider
     * @param sourceCodeHash hash of the requested data
     */
    function _updateDataReceivedBlock(Lib.Provider storage provider, bytes32 sourceCodeHash) internal returns (bool) {
        Lib.JobStorage storage jobSt = provider.jobSt[sourceCodeHash]; // only provider can update receied job only to itself
        if (jobSt.receivedBlock.add(jobSt.storageDuration) < block.number) {
            // required remaining time to cache should be 0
            return false;
        }
        // provider can only update the block.number
        jobSt.receivedBlock = uint32(block.number) - 1;
        return true;
    }

    function _calculateComputationalCost(
        Lib.ProviderInfo memory info,
        uint16[] memory core,
        uint16[] memory runTime
    ) internal pure returns (uint256 sum) {
        uint256 totalRunTime;
        for (uint256 i = 0; i < core.length; i++) {
            uint256 computationalCost = uint256(info.priceCoreMin).mul(uint256(core[i]).mul(uint256(runTime[i])));
            totalRunTime = totalRunTime.add(runTime[i]);
            // total execution time of the workflow should be shorter than a day
            require(core[i] <= info.availableCore && computationalCost > 0 && totalRunTime <= 1440);
            sum = sum.add(computationalCost);
        }
        return sum;
    }

    function _checkRegisteredData(
        uint32 dataPricesSetBlockNum,
        Lib.RegisteredData storage registeredData,
        uint32 cacheCost
    ) internal view returns (uint256, uint32) {
        // if true, then used cluster's registered data if exists
        if (dataPricesSetBlockNum > 0) {
            if (registeredData.committedBlock.length > 0) {
                uint32[] memory dataCommittedBlocks = registeredData.committedBlock;
                uint32 dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 1];
                if (dataPriceSetBlockNum > block.number) {
                    // obtain the committed prices before the block number
                    dataPriceSetBlockNum = dataCommittedBlocks[dataCommittedBlocks.length - 2];
                }
                require(dataPriceSetBlockNum == dataPriceSetBlockNum);
                // data is provided by the provider with its own price
                uint32 _dataPrice = registeredData.dataInfo[dataPriceSetBlockNum].price;
                if (_dataPrice > 1) {
                    cacheCost = cacheCost.add(_dataPrice);
                }
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
        uint32[] memory storageDuration,
        Lib.ProviderInfo memory info
    )
        internal
        returns (
            uint256 sum,
            uint32 _dataTransferIn,
            uint256 storageCost,
            uint32 cacheCost
        )
    {
        uint256 temp;
        for (uint256 i = 0; i < sourceCodeHash.length; i++) {
            bytes32 _sourceCodeHash = sourceCodeHash[i];
            Lib.JobStorage storage jobSt = provider.jobSt[_sourceCodeHash];
            Lib.Storage storage storageInfo = provider.storageInfo[msg.sender][_sourceCodeHash];
            // temp used for _receivedForStorage variable
            temp = storageInfo.received;
            if (temp > 0 && jobSt.receivedBlock + jobSt.storageDuration < block.number) {
                storageInfo.received = 0;
                address _provider = args.provider;
                balances[_provider] += temp; // transfer storagePayment back to provider
                _cleanJobStorage(jobSt);
                emit LogDepositStorage(args.provider, temp);
            }

            if (
                !(storageInfo.received > 0 ||
                    (jobSt.receivedBlock + jobSt.storageDuration >= block.number &&
                        !jobSt.isPrivate &&
                        jobSt.isVerifiedUsed))
            ) {
                Lib.RegisteredData storage registeredData = provider.registeredData[_sourceCodeHash];
                // temp used for returned bool value True or False
                (temp, cacheCost) = _checkRegisteredData(args.dataPricesSetBlockNum[i], registeredData, cacheCost);
                if (temp == 0) {
                    // If returned value of _checkRegisteredData is False move on to next condition
                    if (jobSt.receivedBlock + jobSt.storageDuration < block.number) {
                        if (storageDuration[i] > 0) {
                            jobSt.receivedBlock = uint32(block.number);
                            // Hour is converted into block time, 15 seconds of block time is
                            // fixed and set only one time till the storage time expires
                            jobSt.storageDuration = storageDuration[i].mul(ONE_HOUR_BLOCK_DURATION);
                            // temp used for storageCostTemp variable
                            temp = info.priceStorage.mul(dataTransferIn[i].mul(storageDuration[i]));
                            storageInfo.received = uint248(temp);
                            storageCost = storageCost.add(temp); //storageCost
                            if (args.cacheType[i] == uint8(Lib.CacheType.PRIVATE)) {
                                jobSt.isPrivate = true; // Set by the data owner
                            }
                        } else cacheCost = cacheCost.add(info.priceCache.mul(dataTransferIn[i])); // cacheCost
                    } else {  // data~n is stored (privatley or publicly) on the provider
                        if (
                            storageInfo.received == 0 && // checks whether the user is owner of the data file
                            jobSt.isPrivate == true
                        ) cacheCost = cacheCost.add(info.priceCache.mul(dataTransferIn[i]));
                    }
                    // communication cost should be applied
                    _dataTransferIn = _dataTransferIn.add(dataTransferIn[i]);
                    // owner of the sourceCodeHash is also detected, first time usage
                    emit LogDataStorageRequest(args.provider, msg.sender, _sourceCodeHash);
                } else emit LogRegisteredDataRequestToUse(args.provider, _sourceCodeHash);
            }
        }
        // priceDataTransfer * (dataTransferIn + dataTransferOut)
        sum = sum.add(info.priceDataTransfer.mul(_dataTransferIn.add(args.dataTransferOut)));
        sum = sum.add(storageCost).add(cacheCost); // storageCost + cacheCost
        return (sum, _dataTransferIn, uint32(storageCost), uint32(cacheCost));
    }

    /**
     * @dev Clean storage struct storage (JobStorage, Storage) corresponding mapped sourceCodeHash
     */
    function _cleanJobStorage(Lib.JobStorage storage jobSt) internal {
        delete jobSt.receivedBlock;
        delete jobSt.storageDuration;
        delete jobSt.isPrivate;
        delete jobSt.isVerifiedUsed;
    }

    function _logProcessPayment(
        string memory key,
        Lib.JobIndexes memory args,
        bytes32 resultIpfsHash,
        address recipient,
        uint256 receivedGwei,
        uint256 refundedGwei
    ) internal {
        emit LogProcessPayment(
            msg.sender,
            key,
            args.index,
            args.jobID,
            args.elapsedTime,
            recipient,
            receivedGwei,
            refundedGwei,
            resultIpfsHash,
            args.dataTransferIn,
            args.dataTransferOut
        );
    }

    function emitLogJob(
        string memory key,
        uint32 index,
        bytes32[] memory codeHashes,
        Lib.JobArgument memory args,
        uint256 refunded,
        uint msg_value
    ) internal {
        emit LogJob(
            args.provider,
            msg.sender,
            key,
            index,
            args.cloudStorageID,
            codeHashes,
            args.cacheType,
            args.core,
            args.runTime,
            msg_value,  // msg.value.div(1 gwei)
            refunded
        );
    }

    /* ===============================================PUBLIC_GETTERS=============================================== */
    /**
     * @dev Returns balance of the requested address in Gwei. It takes a
       provider's Ethereum address as parameter.

     * @param owner The address of the requester or provider.
     */
    function balanceOf(address owner) external view returns (uint256) {
        return balances[owner];
    }

    /**
     * @dev Get balance on eBlocBroker
     */
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /**
     * @dev Returns the owner of the eBlocBroker contract
     */
    function getOwner() external view returns (address) {
        return owner;
    }

    /* Returns a list of registered/updated provider's registered data prices */
    function getRegisteredDataBlockNumbers(address provider, bytes32 sourceCodeHash)
        external
        view
        returns (uint32[] memory)
    {
        return providers[provider].registeredData[sourceCodeHash].committedBlock;
    }

    /**
     * @dev Get balance on eBlocBroker.
     *
     * If `pricesSetBn` is 0, it will return the current price at the
     * current block-number that is called
     * If mappings does not valid, then it will return (0, 0)
     */
    function getRegisteredDataPrice(
        address provider,
        bytes32 sourceCodeHash,
        uint32 pricesSetBn
    ) public view returns (Lib.DataInfo memory) {
        Lib.RegisteredData storage registeredData = providers[provider].registeredData[sourceCodeHash];
        if (pricesSetBn == 0) {
            uint32[] memory _dataPrices = registeredData.committedBlock;
            pricesSetBn = _dataPrices[_dataPrices.length - 1];
            if (pricesSetBn > block.number) {
                // Obtain the committed data price before the block.number
                pricesSetBn = _dataPrices[_dataPrices.length - 2];
            }
        }

        return (registeredData.dataInfo[pricesSetBn]);
    }

    function getOrcID(address user) public view returns (bytes32) {
        return orcID[user];
    }

    /* @dev Returns the enrolled requester's block number of the enrolled
       requester, which points to the block that logs `LogRequester event.  It
       takes Ethereum address of the requester, which can be obtained by calling
       LogRequester event.
    */
    function getRequesterCommittmedBlock(address requester) public view returns (uint32) {
        return requesterCommittedBlock[requester];
    }

    /* @dev Returns the registered provider's information. It takes Ethereum
       address of the provider, which can be obtained by calling
       getProviderAddresses If the pricesSetBn is 0, then it will return
       the current price at the current block-number that is called
    */
    function getProviderInfo(address provider, uint32 pricesSetBn)
        public
        view
        returns (uint32, Lib.ProviderInfo memory)
    {
        uint32[] memory providerInfo = pricesSetBlockNum[provider];

        if (pricesSetBn == 0) {
            pricesSetBn = providerInfo[providerInfo.length - 1];
            if (pricesSetBn > block.number) {
                // Obtain the committed prices before the block number
                pricesSetBn = providerInfo[providerInfo.length - 2];
            }
        }
        return (pricesSetBn, providers[provider].info[pricesSetBn]);
    }

    /**
     * @dev Returns various information about the submitted job such as the hash
     * of output files generated by IPFS, UNIX timestamp on job's start time,
     * received Gwei value from the client etc.
     *
     * @param provider The address of the provider.
     * @param key The string of the key.
     */
    function getJobInfo(
        address provider,
        string memory key,
        uint32 index,
        uint256 jobID
    )
        public
        view
        returns (
            Lib.Job memory,
            uint256,
            address,
            uint256,
            uint256
        )
    {
        Lib.Status storage jobInfo = providers[provider].jobStatus[key][index];
        // Lib.Job storage job = jobInfo.jobs[jobID];
        return (jobInfo.jobs[jobID], jobInfo.received, jobInfo.jobOwner, jobInfo.dataTransferIn, jobInfo.dataTransferOut);
    }

    function getProviderPrices(
        address provider,
        string memory key,
        uint256 index
    ) public view returns (Lib.ProviderInfo memory) {
        Lib.Status storage jobInfo = providers[provider].jobStatus[key][index];
        Lib.ProviderInfo memory providerInfo = providers[provider].info[jobInfo.pricesSetBlockNum];
        return (providerInfo);
    }

    /* Returns a list of registered/updated provider's block number */
    function getUpdatedProviderPricesBlocks(address provider) external view returns (uint32[] memory) {
        return pricesSetBlockNum[provider];
    }

    function getJobSize(address provider, string memory key) public view returns (uint256) {
        require(providers[msg.sender].committedBlock > 0);
        return providers[provider].jobStatus[key].length;
    }

    /* Returns a list of registered provider Ethereum addresses */
    function getProviders() external view returns (address[] memory) {
        return registeredProviders;
    }

    /* @dev Checks whether or not the given Ethereum address of the provider is
       already registered in eBlocBroker.
     */
    function doesProviderExist(address provider) external view returns (bool) {
        return providers[provider].committedBlock > 0;
    }

    /* @dev Checks whether or not the enrolled requester's given ORCID iD is
       already authenticated in eBlocBroker. */
    function isOrcIDVerified(address user) external view returns (bool) {
        if (orcID[user] == "") return false;
        return true;
    }

    /**
     * @dev Checks whether or not the given Ethereum address of the requester
     * is already registered in eBlocBroker.
     *
     * @param requester The address of requester
     */
    function doesRequesterExist(address requester) public view returns (bool) {
        return requesterCommittedBlock[requester] > 0;
    }

    function getStorageInfo(
        address provider,
        address requester,
        bytes32 codeHash
    ) external view returns (uint256, Lib.JobStorage memory) {
        Lib.Provider storage _provider = providers[provider];
        require(_provider.isRunning);
        if (requester == address(0)) {
            return (0, _provider.jobSt[codeHash]);
        }
        return (_provider.storageInfo[requester][codeHash].received, _provider.jobSt[codeHash]);
    }

    /**
     * @dev Returns block numbers where provider's prices are set
     * @param provider The address of the provider
     */
    function getProviderSetBlockNumbers(address provider) external view returns (uint32[] memory) {
        return pricesSetBlockNum[provider];
    }

    // used for tests
    // ==============
    function getProviderReceiptNode(address provider, uint32 index) external view returns (uint32, uint256, int32) {
        return providers[provider].receiptList.printIndex(index);
    }
}
