// SPDX-License-Identifier: MIT

/*
  file:   Lib.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity >=0.7.0 <0.9.0;

library Lib {
    enum CacheType {
        PUBLIC, /* 0 */
        PRIVATE /* 1 */
    }

    enum CloudStorageID {
        IPFS, /* 0 */
        IPFS_GPG, /* 1 */
        NONE, /* 2 Request to use from registered/cached data */
        EUDAT, /* 3 */
        GDRIVE /* 4 */
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
         * provider that is requested to run the job. */
        address payable provider;
        /* A uint32 value containing the block number when the requested
         * provider set its prices most recent. */
        uint32 priceBlockIndex;
        /* An array of uint8 values that denote whether the requester’s data is
           stored and shared using either IPFS, EUDAT, IPFS (with GPG
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
        uint16[] runTime;
        uint32 dataTransferOut;
    }

    struct JobIndexes {
        uint32 index;
        uint32 jobID;
        uint32 endTimestamp;
        uint32 dataTransferIn;
        uint32 dataTransferOut;
        uint32 elapsedTime;
        uint256[] core;
        uint256[] runTime;
        bool endJob;
    }

    struct DataInfo {
        uint32 price;
        uint32 commitmentBlockDur;
    }

    struct Storage {
        uint256 received; // received payment for storage usage
    }

    struct JobStorage {
        uint32 receivedBlock;
        uint32 storageDuration;
        bool isPrivate;
        bool isVerifiedUsed; // Set to `true` if the provided used and verified the given code hash
        //address      owner; //Cloud be multiple owners
    }

    struct RegisteredData {
        uint32[] committedBlock; // Block number when data is registered
        mapping(uint256 => DataInfo) dataInfo;
    }

    struct Job {
        JobStateCodes stateCode; // Assigned by the provider
        uint32 startTimestamp; // Submitted job's starting universal time on the server side. Assigned by the provider
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
        uint32 commitmentBlockDur;
        /* All the price varaibles are defined in Gwei.
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
        mapping(bytes32 => JobStorage) jobSt; // Stored information related to job's storage time
        mapping(bytes32 => RegisteredData) registeredData;
        mapping(address => mapping(bytes32 => Storage)) storageInfo;
        mapping(string => Status[]) jobStatus; // All submitted jobs into provider 's Status is accessible
        LL receiptList; // receiptList will be use to check either job's start and end time overlapped or not
    }

    struct Interval {
        int32 core; // job's requested core number
        uint32 next; // points to next the node
        uint32 endpoint;
    }

    struct IntervalArg {
        uint32 startTimestamp;
        uint32 endTimestamp;
        int32 core; // job's requested core number
        int256 availableCore;
    }

    struct LL {
        uint32 length;
        uint32 tail; // tail of the linked list
        mapping(uint256 => Interval) items;
    }

    /**
     *@dev Invoked when registerProvider() function is called
     *@param self | Provider struct
     */
    function construct(Provider storage self) internal {
        self.isRunning = true;
        self.committedBlock = uint32(block.number);
        self.receiptList.length = 1; // trick to show mapped index(0)'s values as zero
    }

    function push(
        LL storage self,
        uint256 next,
        uint32 endpoint,
        int32 core,
        uint32 idx
    ) internal {
        self.items[idx].endpoint = endpoint;
        self.items[idx].core = core;
        self.items[idx].next = uint32(next);
    }

    function _recursive(Interval storage self)
        internal
        view
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
        uint256 currentNodeIndex,
        uint256 prevNodeIndex,
        uint32 _length,
        int32 carriedSum,
        Lib.IntervalArg memory _interval
    ) internal returns (bool) {
        // int32 carriedSum = core; // Carried sum variable is assigned with job's given core number
        uint256 currentNodeEndpoint = self.items[currentNodeIndex].endpoint; // read from the storage
        int32 currentNodeCore = self.items[currentNodeIndex].core;
        uint32 currentNodeNext = self.items[currentNodeIndex].next;
        do {
            if (_interval.startTimestamp >= currentNodeEndpoint) {
                if (_interval.startTimestamp == currentNodeEndpoint) {
                    int32 temp = currentNodeCore + (_interval.core * -1);
                    if (temp == 0) {
                        self.items[prevNodeIndex].next = currentNodeNext;
                        delete self.items[currentNodeIndex]; // length of the list is not incremented
                        self.length = _length; // !!! !!!! !!!
                    } else {
                        if (temp > _interval.availableCore) return false;
                        self.items[currentNodeIndex].core = temp;
                        self.length = _length;
                    }
                    return true;
                } else {
                    /* Covers [val, val1) s = s-1 */
                    push(self, self.items[prevNodeIndex].next, _interval.startTimestamp, _interval.core * -1, _length);
                    self.items[prevNodeIndex].next = _length;
                    self.length = _length + 1;
                    return true;
                }
            }
            /* Inside while loop carriedSum is updated. If enters into if statement it
            means revert() is catched and all the previous operations are reverted back */
            carriedSum += currentNodeCore;
            if (carriedSum > _interval.availableCore) {
                return false;
            }
            prevNodeIndex = currentNodeIndex;
            currentNodeIndex = currentNodeNext; // already in the memory, cheaper
            currentNodeEndpoint = self.items[currentNodeIndex].endpoint; // read from the storage
            currentNodeCore = self.items[currentNodeIndex].core;
            currentNodeNext = self.items[currentNodeIndex].next;
        } while (true);
    }

    function _iterateStart(
        LL storage self,
        uint256 prevNodeIndex,
        uint256 currentNodeIndex,
        Lib.IntervalArg memory _interval
    )
        internal
        returns (
            uint256 flag,
            uint256 _addr,
            uint256,
            int32 carriedSum,
            uint32 prevNodeIndexNextTemp,
            int32 updatedCoreVal
        )
    {
        flag = 1;
        uint32 currentNodeEndpoint = self.items[prevNodeIndex].endpoint;
        uint32 currentNodeNext = self.items[prevNodeIndex].next;
        int32 currentNodeCore = self.items[prevNodeIndex].core;
        int32 temp;
        do {
            /* Inside while loop carriedSum is updated. If enters into if statement it
            means revert() is catched and all the previous operations are reverted back */
            if (_interval.endTimestamp >= currentNodeEndpoint) {
                carriedSum += _interval.core;
                if (carriedSum > _interval.availableCore) return (0, _addr, 0, 0, 0, 0);

                if (_interval.endTimestamp == currentNodeEndpoint) {
                    temp = currentNodeCore + int32(_interval.core);
                    carriedSum += currentNodeCore;
                    if (carriedSum > _interval.availableCore || temp > _interval.availableCore)
                        return (0, _addr, 0, 0, 0, 0);

                    if (temp != 0) {
                        flag = 2; // helps to prevent pushing since it is already added
                    } else {
                        flag = 3; // helps to prevent pushing since it is already added
                        prevNodeIndexNextTemp = self.items[prevNodeIndex].next;
                        self.items[currentNodeIndex] = self.items[currentNodeNext];
                    }
                }
                _addr = currentNodeIndex; /* "addr" points the index to be added into the linked list */
                return (flag, _addr, prevNodeIndex, carriedSum, prevNodeIndexNextTemp, temp);
            }
            carriedSum += currentNodeCore;
            if (carriedSum > _interval.availableCore) {
                return (0, _addr, 0, 0, 0, 0);
            }
            prevNodeIndex = currentNodeIndex;
            currentNodeIndex = currentNodeNext;
            currentNodeEndpoint = self.items[currentNodeIndex].endpoint;
            currentNodeNext = self.items[currentNodeIndex].next;
            currentNodeCore = self.items[currentNodeIndex].core;
        } while (true);
    }

    function overlapCheck(LL storage self, IntervalArg memory _interval) internal returns (uint256 flag) {
        uint256 addr = self.tail;
        uint256 addrTemp;
        uint256 prevNodeIndex;
        uint256 currentNodeIndex;
        uint256 prevNodeIndexNextTemp;
        int32 carriedSum;
        int32 updatedCoreVal;
        if (_interval.endTimestamp <= self.items[addr].endpoint) {
            /* Current node points index of previous tail-node right after the insert operation */
            currentNodeIndex = prevNodeIndex = addr;
            (flag, addr, prevNodeIndex, carriedSum, prevNodeIndexNextTemp, updatedCoreVal) = _iterateStart(
                self,
                prevNodeIndex,
                currentNodeIndex,
                _interval
            );
            if (flag == 0) {
                return 0; // false
            }
        }
        uint256 _length = self.length;
        if (flag <= 1) {
            /* inserted while keeps sorted order */
            push(self, addr, _interval.endTimestamp, _interval.core, uint32(_length));
            _length += 1;
            carriedSum = _interval.core;
            if (flag == 0) {
                addrTemp = addr;
                prevNodeIndex = self.tail = uint32(_length - 1);
            } else {
                addrTemp = self.items[prevNodeIndex].next;
                self.items[prevNodeIndex].next = uint32(_length - 1);
                prevNodeIndex = uint32(_length - 1);
            }
        }
        if (flag > 1) {
            addrTemp = self.items[prevNodeIndex].next;
        }
        currentNodeIndex = addrTemp; //self.items[prevNodeIndex].next;
        if (_iterate(self, currentNodeIndex, prevNodeIndex, uint32(_length), carriedSum, _interval)) {
            if (flag == 2) {
                self.items[addr].core = updatedCoreVal;
            }
            return 1; // true
        } else {
            if (flag <= 1) {
                delete self.items[uint32(_length - 1)];
                if (prevNodeIndex == self.tail) self.tail = uint32(addrTemp);
                else self.items[prevNodeIndex].next = uint32(addrTemp); // change on the contract storage
            } else if (flag == 3) {
                self.items[prevNodeIndex].next = uint32(prevNodeIndexNextTemp);
            }
            return 0; // false
        }
    }

    /* used for test getReceiptListSize */
    function printIndex(LL storage self, uint32 index) external view returns (uint32, uint256 idx, int32) {
        idx = self.tail;
        for (uint256 i = 0; i < index; i++) {
            idx = self.items[idx].next;
        }
        // self.length: receipt_list_size
        return (self.length, self.items[idx].endpoint, self.items[idx].core);
    }
}
