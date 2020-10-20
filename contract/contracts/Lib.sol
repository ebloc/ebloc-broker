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

    struct Interval {
        uint32 next; // Points to next the node
        uint32 endpoint;
        int32 core; // Job's requested core number
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
        uint32 startTime; // Submitted job's starting universal time on the server side. Assigned by the provider
        JobStateCodes jobStateCode; // Assigned by the provider
        // uint16 core;                // Requested core array by the client
        // uint16 executionDuration;    // Time to run job in minutes. ex: minute + hour * 60 + day * 1440; assigned by the client
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
        mapping(string => Status[]) jobStatus; // All submitted jobs into provider 's Status is accessible
        mapping(uint256 => ProviderInfo) info;
        mapping(bytes32 => JobStorageTime) jobSt; // Stored information related to job's storage time
        mapping(bytes32 => RegisteredData) registeredData;
        mapping(address => mapping(bytes32 => Storage)) storageInfo;
        IntervalNode receiptList; // receiptList will be use to check either job's start and end time overlapped or not
    }

    struct IntervalNode {
        uint32 tail; // tail of the linked list
        uint32 deletedItemNum; // keep track of deleted nodes
        Interval[] list; // A dynamically-sized array of interval structs
    }

    /**
     *@dev Invoked when registerProvider() function is called
     *@param self | Provider struct
     */
    function constructProvider(Provider storage self) internal {
        self.isRunning = true;
        self.committedBlock = uint32(block.number);
        IntervalNode storage receiptList = self.receiptList;
        receiptList.list.push(Interval({next: 0, endpoint: 0, core: 0})); /* Dummy node is inserted on initialization */
    }

    function _isOverlapAlgorithm(
        uint32 prevNode_next,
        uint32 startTime,
        int32 carriedSum, /* assigned with job's given core number */
        int32 availableCore,
        int32 core,
        Interval storage prevNode_storage,
        Interval[] storage list
    ) internal returns (bool flag, bool isDeleted) {
        Interval memory currentNode = list[prevNode_next]; /* Current node points index before insert operation is done */
        Interval memory prevNode = prevNode_storage;
        do {
            /* Covers [val, val1) s = s-1 */
            if (startTime >= currentNode.endpoint) {
                if (startTime == currentNode.endpoint) {
                    int32 temp = currentNode.core + (int32(core) * -1);
                    if (temp != 0) {
                        list[prevNode.next].core = currentNode.core + (int32(core) * -1);
                    }

                    prevNode_storage.next = list[prevNode.next].next;
                    delete list[prevNode.next];
                    isDeleted = true;
                } else {
                    list.push(Interval({next: prevNode.next, endpoint: startTime, core: int32(core) * -1}));
                    if (!flag) {
                        prevNode_storage.next = uint32(list.length - 1);
                    } else {
                        // additional 5k storage for read from the list
                        list[prevNode_next].next = uint32(list.length - 1);
                    }
                }
                return (true, isDeleted);
            }
            carriedSum += currentNode.core; /* Inside while loop carriedSum is updated */
            /* If enters into if statement it means revert() is catched and all
               the previous operations are reverted back */
            if (carriedSum > availableCore) {
                return (false, false);
            }
            prevNode_next = prevNode.next;
            prevNode = currentNode;
            currentNode = list[currentNode.next];
            flag = true;
        } while (true);
    }

    function checkIfOverlapExists(
        IntervalNode storage self,
        uint32 startTime,
        uint32 completionTime,
        int32 availableCore,
        uint256 core
    ) internal returns (bool flag) {
        Interval[] storage list = self.list;
        uint32 addrTemp;
        uint32 addr = self.tail;

        Interval storage prevNode = list[0];
        Interval storage currentNode = prevNode;
        Interval storage prevNodeTemp = prevNode;

        if (completionTime < list[addr].endpoint) {
            flag = true;
            prevNode = list[addr];
            /* Current node points index of previous tail-node right after the insert operation */
            currentNode = list[prevNode.next];
            do {
                if (completionTime > currentNode.endpoint) {
                    addr = prevNode.next; /* "addr" points the index to the pushed the node */
                    break;
                }
                prevNode = currentNode;
                currentNode = list[currentNode.next];
            } while (true);
        }

        /* Inserted while keeping the sorted order */
        list.push(Interval({next: addr, endpoint: completionTime, core: int32(core)}));

        if (!flag) {
            addrTemp = addr;
            prevNode = list[self.tail = uint32(list.length - 1)];
        } else {
            addrTemp = prevNode.next;
            prevNodeTemp = prevNode;
            /* Node that pushed in-between the linked-list, additional 5k storage for read from the list */
            prevNode.next = uint32(list.length - 1);
        }

        (bool isOverlapFlag, bool isDeleted) = _isOverlapAlgorithm(
            prevNode.next,
            startTime,
            int32(core),
            availableCore,
            int32(core),
            prevNode,
            list
        );
        if (isOverlapFlag) {
            if (isDeleted) self.deletedItemNum += 1;
            return true;
        } else {
            delete list[list.length - 1];
            if (!flag) {
                self.tail = addrTemp;
            } else {
                prevNodeTemp.next = addrTemp; // change on storage
            }
            self.deletedItemNum += 1;
            return false;
        }
    }

    /* Used for tests */
    function getReceiptListSize(IntervalNode storage self) external view returns (uint32) {
        return uint32(self.list.length - self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(IntervalNode storage self, uint32 index) external view returns (uint256, int32) {
        uint32 _index = self.tail;
        for (uint256 i = 0; i < index; i++) {
            _index = self.list[_index].next;
        }
        return (self.list[_index].endpoint, self.list[_index].core);
    }
}
