// SPDX-License-Identifier: MIT

/*
  file:   Lib.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity 0.7.0;

library Lib {
    enum CacheType {
        PUBLIC, /* 0 */
        PRIVATE /* 1 */
    }

    enum CloudStorageID {
        IPFS, /* 0 */
        EUDAT, /* 1 */
        IPFS_MINILOCK, /* 2 */
        GITHUB, /* 3 */
        GDRIVE, /* 4 */
        NONE /* 5 Requested to use from registered data */
    }

    /* Status of the submitted job Enum */
    enum JobStateCodes {
        /* Following states {0, 1, 2} will allow to request refund */
        SUBMITTED, /* 0 Initial state */
        PENDING,
        /* 1 Indicates when a request is receieved by the provider. The
         * job is waiting for resource allocation. It will eventually
         * run. */
        RUNNING,
        /* 2 The job currently is allocated to a node and is
         * running. Corresponding data files are downloaded and
         * verified.*/
        /* Following states {3, 4, 5} used to prevent double spending */
        REFUNDED, /* 3 Indicates if job is refunded */
        CANCELLED,
        /* 4 Job was explicitly cancelled by the requester or system
         * administrator. The job may or may not have been
         * initiated. Set by the requester*/
        COMPLETED,
        /* 5 The job has completed successfully and deposit is paid
         * to the provider */
        TIMEOUT, /* 6 Job terminated upon reaching its time limit. */
        COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT /* 7  */
    }

    struct JobArgument {
        /* An Ethereum address value containing the Ethereum address of the
           provider that is requested to run the job. */
        address payable provider;
        /* A uint32 value containing the block number when the requested
         * provider set its prices most recent. */
        uint32 providerPriceBlockIndex;
        /* An array of uint8 values that denote whether the requester’s data is
           stored and shared using either IPFS, EUDAT, IPFS (with MiniLock
           encryption), or Google Drive. */
        uint8[] cloudStorageID;
        /* An array of uint8 values that denote whether the requester’s data
            will be cached privately within job owner's home directory, or
            publicly for other requesters' access within a shared directory for
            all the requesters.
         */
        uint8[] cacheType;
        /* An array of uint32 values that denote whether the provider’s
         * registered data will be used or not. */
        uint32[] dataPricesSetBlockNum;
        uint16[] core;
        uint16[] executionDuration;
        uint32 dataTransferOut;
    }

    struct JobIndexes {
        uint32 index;
        uint32 jobID;
        uint32 completionTime;
        uint32 dataTransferIn;
        uint32 dataTransferOut;
        uint256[] core;
        uint256[] executionDuration;
        bool endJob;
    }

    struct DataInfo {
        uint32 price;
        uint32 commitmentBlockDuration;
    }

    struct Storage {
        uint256 received; // Received payment for storage usage
    }

    struct JobStorageTime {
        uint32 receivedBlock;
        uint32 storageDuration;
        bool isPrivate;
        bool isVerifiedUsed; // Set to True if the requester is used and verified the given sourceCodeHash
        //address      owner; //Cloud be multiple owners
    }

    struct RegisteredData {
        uint32[] committedBlock; // Block number when data is registered
        mapping(uint256 => DataInfo) dataInfo;
    }

    struct Job {
        JobStateCodes jobStateCode; // Assigned by the provider
        uint32 startTime; // Submitted job's starting universal time on the server side. Assigned by the provider
    }

    // Submitted Job's information
    struct Status {
        uint32 cacheCost;
        uint32 dataTransferIn;
        uint32 dataTransferOut;
        uint32 pricesSetBlockNum; // When provider is submitted provider's most recent block number when its set or updated
        uint256 received; // Paid amount (new owned) by the client
        address payable jobOwner; // Address of the client (msg.sender) has been stored
        bytes32 sourceCodeHash; // keccak256 of the list of sourceCodeHash list concatinated with the cacheType list
        bytes32 jobInfo;
        mapping(uint256 => Job) jobs;
    }

    struct ProviderInfo {
        uint32 availableCore; // Registered core number of the provider
        uint32 commitmentBlockDuration;
        /* All the price varaibles are defined in Wei.
           Floating-point or fixed-point decimals have not yet been implemented in Solidity */
        uint32 priceCoreMin; // Provider's price for core per minute
        uint32 priceDataTransfer;
        uint32 priceStorage;
        uint32 priceCache;
    }

    struct Provider {
        uint32 committedBlock; // Block number when  is registered in order the watch provider's event activity
        bool isRunning; // Flag that checks is Provider running or not
        mapping(uint256 => ProviderInfo) info;
        mapping(bytes32 => JobStorageTime) jobSt; // Stored information related to job's storage time
        mapping(bytes32 => RegisteredData) registeredData;
        mapping(address => mapping(bytes32 => Storage)) storageInfo;
        mapping(string => Status[]) jobStatus; // All submitted jobs into provider 's Status is accessible
        IntervalNode receiptList; // receiptList will be use to check either job's start and end time overlapped or not
    }

    struct Interval {
        int32 core; // Job's requested core number
        uint32 next; // Points to next the node
        uint32 endpoint;
    }

    struct LL {
        uint32 length;
        mapping(uint256 => Interval) items;
    }

    struct IntervalNode {
        uint32 tail; // Tail of the linked list
        LL ll;
    }

    /**
     *@dev Invoked when registerProvider() function is called
     *@param self | Provider struct
     */
    function constructProvider(Provider storage self) internal {
        self.isRunning = true;
        self.committedBlock = uint32(block.number);
        push(self.receiptList.ll, 0, 0, 0, 0); /* Dummy node is inserted on initialization // Not needed */
        self.receiptList.ll.length = 1;
    }

    function push(
        LL storage self,
        uint256 next,
        uint32 endpoint,
        int32 core,
        uint32 length
    ) internal {
        self.items[length].endpoint = endpoint;
        self.items[length].core = core;
        self.items[length].next = uint32(next);
    }

    function _recursive(Interval storage self)
        internal
        returns (
            uint32,
            uint32,
            int32
        )
    {
        return (self.next, self.endpoint, self.core);
    }

    function _iterate(
        LL storage self,
        int32 core,
        uint32 startTime,
        uint256 currentNode_index,
        uint256 prevNode_index,
        int32 availableCore,
        uint32 _length
    ) internal returns (bool) {
        int32 carriedSum = core; // Carried sum variable is assigned with job's given core number
        uint256 currentNode_endpoint = self.items[currentNode_index].endpoint; // read from the storage
        int32 currentNode_core = self.items[currentNode_index].core;
        uint32 currentNode_next = self.items[currentNode_index].next;
        do {
            if (startTime >= currentNode_endpoint) {
                if (startTime == currentNode_endpoint) {
                    int32 temp = currentNode_core + (core * -1);
                    if (temp == 0) {
                        self.items[prevNode_index].next = self.items[currentNode_index].next;
                        delete self.items[currentNode_index]; // length of the list is not incremented
                    }
                    self.items[currentNode_index].core = temp;
                    self.length = _length; // length without incremented since there was no added variable
                    return true;
                } else {
                    /* Covers [val, val1) s = s-1 */
                    push(self, self.items[prevNode_index].next, startTime, core * -1, _length);
                    self.items[prevNode_index].next = _length;
                    self.length = _length + 1;
                    return true;
                }
            }
            carriedSum += currentNode_core; /* Inside while loop carriedSum is updated */
            /* If enters into if statement it means revert() is catched and all
               the previous operations are reverted back */
            if (carriedSum > availableCore) return false;

            prevNode_index = currentNode_index;
            currentNode_index = currentNode_next; // already in the memory, cheaper
            currentNode_endpoint = self.items[currentNode_index].endpoint; // read from the storage
            currentNode_core = self.items[currentNode_index].core;
            currentNode_next = self.items[currentNode_index].next;
        } while (true);
    }

    function checkIfOverlapExists(
        IntervalNode storage self,
        uint32 startTime,
        uint32 completionTime,
        int32 availableCore,
        uint256 core
    ) internal returns (bool flag) {
        LL storage ll = self.ll;

        uint256 addrTemp;
        uint256 addr = self.tail;
        uint256 prevNode_index;
        uint256 currentNode_index;
        if (completionTime < ll.items[addr].endpoint) {
            flag = true;
            prevNode_index = addr;
            /* Current node points index of previous tail-node right after the insert operation */
            currentNode_index = ll.items[prevNode_index].next;
            uint32 currentNode_endpoint = ll.items[currentNode_index].endpoint;
            uint32 currentNode_next = ll.items[currentNode_index].next;
            do {
                if (completionTime > currentNode_endpoint) {
                    addr = currentNode_index; /* "addr" points the index to be added into the linked list */
                    break;
                }
                prevNode_index = currentNode_index;
                currentNode_index = currentNode_next;
                currentNode_endpoint = ll.items[currentNode_index].endpoint;
                currentNode_next = ll.items[currentNode_index].next;
            } while (true);
        }

        uint256 _length = ll.length;
        /* Inserted while keeping sorted order */
        push(ll, addr, completionTime, int32(core), uint32(_length));
        _length += 1;

        if (!flag) {
            addrTemp = addr;
            prevNode_index = self.tail = uint32(_length - 1);
        } else {
            addrTemp = ll.items[prevNode_index].next;
            ll.items[prevNode_index].next = uint32(_length - 1);
        }

        currentNode_index = ll.items[prevNode_index].next;
        if (_iterate(ll, int32(core), startTime, currentNode_index, prevNode_index, availableCore, uint32(_length))) {
            return true;
        } else {
            delete ll.items[uint32(_length - 1)];
            if (!flag) {
                self.tail = uint32(addrTemp);
            } else {
                ll.items[prevNode_index].next = uint32(addrTemp); // change on storage
            }
            return false;
        }
    }

    /* Used for tests */
    function getReceiptListSize(IntervalNode storage self) external view returns (uint32) {
        return self.ll.length;
    }

    /* Used for test */
    function printIndex(IntervalNode storage self, uint32 index) external view returns (uint256 _index, int32) {
        _index = self.tail;
        for (uint256 i = 0; i < index; i++) {
            _index = self.ll.items[_index].next;
        }

        return (self.ll.items[_index].endpoint, self.ll.items[_index].core);
    }
}
