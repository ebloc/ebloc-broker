/*
  file:   Lib.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.6.0;


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
        PENDING, /* 1 Indicates when a request is receieved by the provider. The job is waiting for resource allocation. It will eventually run. */
        RUNNING, /* 2 The job currently is allocated to a node and is running. Corresponding data files are downloaded and verified.*/
        /* Following states {3, 4, 5} used to prevent double spending */
        REFUNDED, /* 3 Indicates if job is refunded */
        CANCELLED, /* 4 Job was explicitly cancelled by the requester or system administrator. The job may or may not have been initiated. Set by the requester*/
        COMPLETED, /* 5 The job has completed successfully and deposit is paid to the provider */
        TIMEOUT, /* 6 Job terminated upon reaching its time limit. */
        COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT /* 7  */
    }

    struct JobArgument {
        address payable provider; /* An Ethereum address value containing the Ethereum address of the provider that is requested to run the job. */
        uint32 providerPriceBlockIndex; /* A uint32 value containing the block number when the requested provider set its prices most recent. */
        uint8[] cloudStorageID; /* An array of uint8 values that denote whether the requester’s data is stored and shared using either IPFS, EUDAT, IPFS (with MiniLock encryption), or Google Drive. */
        uint8[] cacheType; /* An array of uint8 values that denote whether the requester’s data will be cached privately within job owner's home directory, or publicly for other requesters' access within a shared directory for all the requesters. */
        uint32[] dataPricesSetBlockNum; /* An array of uint32 values that denote whether the provider’s registered data will be used or not. */
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

    struct Interval {
        uint32 endpoint;
        int32 core; // Job's requested core number
        uint32 next; // Points to next the node
    }

    struct IntervalNode {
        uint32 tail; // Tail of the linked list
        uint32 deletedItemNum; // Keep track of deleted nodes
        Interval[] list; // A dynamically-sized array of interval structs
    }

    /**
     *@dev Invoked when registerProvider() function is called
     *@param self | Provider struct
     */

    function constructProvider(Provider storage self) internal {
        self.isRunning = true;
        self.committedBlock = uint32(block.number);

        IntervalNode storage selfReceiptList = self.receiptList;
        selfReceiptList.list.push(Interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
    }

    function checkIfOverlapExists(
        IntervalNode storage self,
        Job memory _job,
        uint32 completionTime,
        int32 availableCore,
        uint256 core
    ) internal returns (bool flag) {
        Interval[] storage list = self.list;

        uint32 addrTemp;
        uint32 addr = self.tail;
        uint32 startTime = _job.startTime;
        int32 carriedSum;

        Interval storage prevNode = list[0];
        Interval storage currentNode = list[0];
        Interval storage prevNodeTemp = list[0];

        // +----------------------------+
        // | Begin: isOverlap Algorithm |
        // +----------------------------+

        if (completionTime < list[addr].endpoint) {
            flag = true;
            prevNode = list[addr];
            currentNode = list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

            do {
                if (completionTime > currentNode.endpoint) {
                    addr = prevNode.next; /* "addr" points the index to the pushed the node */
                    break;
                }
                prevNode = currentNode;
                currentNode = list[currentNode.next];
            } while (true);
        }

        list.push(Interval({endpoint: completionTime, core: int32(core), next: addr})); /* Inserted while keeping sorted order */
        carriedSum = int32(core); /* Carried sum variable is assigned with job's given core number */

        if (!flag) {
            addrTemp = addr;
            prevNode = list[self.tail = uint32(list.length - 1)];
        } else {
            addrTemp = prevNode.next;
            prevNodeTemp = prevNode;
            prevNode.next = uint32(list.length - 1); /* Node that pushed in-between the linked-list */
        }

        currentNode = list[prevNode.next]; /* Current node points index before insert operation is done */

        do {
            /* Inside while loop carriedSum is updated */
            if (startTime >= currentNode.endpoint) {
                /* Covers [val, val1) s = s-1 */
                list.push(Interval({endpoint: startTime, core: -1 * int32(core), next: prevNode.next}));
                prevNode.next = uint32(list.length - 1);
                return true;
            }

            carriedSum += currentNode.core;

            /* If enters into if statement it means revert() is catched and all the previous operations are reverted back */
            if (carriedSum > availableCore) {
                delete list[list.length - 1];
                if (!flag) self.tail = addrTemp;
                else prevNodeTemp.next = addrTemp;

                self.deletedItemNum += 1;
                return false;
            }

            prevNode = currentNode;
            currentNode = list[currentNode.next];
        } while (true);

        // +--------------------------+
        // | End: isOverlap Algorithm |
        // +--------------------------+
    }

    /* Used for tests */
    function getReceiptListSize(IntervalNode storage self) external view returns (uint32) {
        return uint32(self.list.length - self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(IntervalNode storage self, uint32 index) external view returns (uint256, int32) {
        uint32 _index = self.tail;
        for (uint256 i = 0; i < index; i++) _index = self.list[_index].next;

        return (self.list[_index].endpoint, self.list[_index].core);
    }
}
