/*
  file:   Lib.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;

library Lib {
    
    enum StorageID
    {
     IPFS,          /* 0 */
     EUDAT,         /* 1 */
     IPFS_MINILOCK, /* 2 */
     GITHUB,        /* 3 */
     GDRIVE         /* 4 */
    }
    
    /* Status of the submitted job */
    enum JobStateCodes
    {
     /* Following states {0, 1, 2} will allow to request refund */
     SUBMITTED,   /* 0 Initial state */
     PENDING,     /* 1 Indicates when a request is receieved by the provider. The job is waiting for resource allocation. It will eventually run. */
     RUNNING,     /* 2 The job currently is allocated to a node and is running. */	
     /* Following states {3, 4, 5} used to prevent double spending */
     COMPLETED,   /* 3 The job has completed successfully. */
     REFUNDED,    /* 4 Indicates if job is refunded */
     CANCELLED,   /* 5 Job was explicitly cancelled by the requester or system administrator. The job may or may not have been initiated. */
     TIMEOUT      /* 6 Job terminated upon reaching its time limit. */
    }

    struct JobArgument {
	uint8[] storageID;
	uint8   cacheType;
	uint32  priceBlockIndex;
    }

    struct JobIndexes {
	uint32 index;
	uint32 jobID;
    }

    struct JobStorageTime {
	uint32 receivedBlock;
	uint32 cacheDuration;
    }

    struct Job {	
	uint32 startTime; // Submitted job's starting universal time on the server side. Assigned by the provider
	JobStateCodes jobStateCode; // Assigned by the provider
	uint16 core;                // Requested core array by the client 
	uint16 executionTimeMin;    // Time to run job in minutes. ex: minute + hour * 60 + day * 1440; assigned by the client	
    }

    // Submitted Job's information
    struct Status {
        uint32         cacheCost;
        uint32    dataTransferIn;
        uint32   dataTransferOut;
        uint            received; // Paid amount (new owned) by the client
        address payable jobOwner; // Address of the client (msg.sender) has been stored
        uint32 pricesSetBlockNum; // When provider is submitted provider's most recent block number when its set or updated
        bytes32   sourceCodeHash; // keccak256 of the list of sourceCodeHash list

        mapping(uint => Job) jobs;
    }
       
    struct Requester {
	uint32 committedBlock; // Block number when provider is registered in order the watch provider's event activity 
	string orcID; // Requester's orcID 
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

    struct Storage {
	uint248 received;
	bool      isUsed; // Received payment for storage usage
    } 
    
    struct Provider {
	uint         received; // Provider's received wei // Address where funds are collected
	uint32 committedBlock; // Block number when  is registered in order the watch provider's event activity
	bool        isRunning; // Flag that checks is Provider running or not 

	mapping(string  => Status[])   jobStatus; // All submitted jobs into provider 's Status is accessible
	mapping(uint256 => ProviderInfo)    info;
	mapping(bytes32 => JobStorageTime) jobSt; // Stored information related to job's storage time 
	mapping(bytes32 => uint256) registeredData;
	mapping(address => mapping(bytes32  => Storage)) storagedData; 
	
	IntervalNode receiptList; // receiptList will be use to check either job's start and end time overlapped or not
    }

    struct Interval {
	uint32 endpoint;
	int32      core; // Job's requested core number
	uint32     next; // Points to next the node 
    }

    struct IntervalNode {
	uint32 tail;           // Tail of the linked list
	uint32 deletedItemNum; // Keep track of deleted nodes 
	Interval[] list;       // A dynamically-sized array of interval structs 
    }    
	
    /**
     *@dev Invoked when registerProvider() function is called 
     *@param self | Provider struct
     */	

    function constructProvider(Provider storage self) internal
    {
	self.isRunning = true;
	self.received;
	self.committedBlock = uint32(block.number);

	IntervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(Interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
	selfReceiptList.tail;	
	selfReceiptList.deletedItemNum;
    }
    
    function receiptCheck(IntervalNode storage self, Job memory _job, uint32 endTime, int32 availableCore) internal
	returns (bool flag)
    {
	Interval[] storage list = self.list;
	
	uint32 addr = self.tail;
	uint32 addrTemp;
	uint32 startTime = _job.startTime;
	int32  carriedSum;	
	
	Interval storage prevNode     = list[0];
	Interval storage currentNode  = list[0];
	Interval storage prevNodeTemp = list[0];

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (endTime < list[addr].endpoint) {
	    flag        = true;
	    prevNode    = list[addr];
	    currentNode = list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { 
		if (endTime > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to the pushed the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = list[currentNode.next];
	    } while (true);
	}

	list.push(Interval({endpoint: endTime, core: int32(_job.core), next: addr})); /* Inserted while keeping sorted order */
	carriedSum = int32(_job.core); /* Carried sum variable is assigned with job's given core number */
	
	if (!flag) {
	    addrTemp      = addr;	    
	    prevNode      = list[self.tail = uint32(list.length - 1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = list[prevNode.next]; /* Current node points index before insert operation is done */
	
	do { /* Inside while loop carriedSum is updated */	    
	    if (startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		prevNode.next = uint32(list.push(Interval({endpoint: startTime, core: -1 * int32(_job.core), next: prevNode.next})) - 1);
		return true;
	    }

	    carriedSum += currentNode.core;
	    
	    /* If enters into if statement it means revert() is catched and all the previous operations are reverted back */
	    if (carriedSum > availableCore) {			    
		delete list[list.length - 1];
		if (!flag)
		    self.tail = addrTemp;
		else
		    prevNodeTemp.next = addrTemp;

		self.deletedItemNum += 1;
		return false;
	    }

	    prevNode    = currentNode;
	    currentNode = list[currentNode.next];
	} while (true);

	// +-----------------------------+
	// | End: receiptCheck Algorithm |
	// +-----------------------------+
    }

    /* Used for tests */
    function getReceiptListSize(IntervalNode storage self) external view
	returns (uint32)
    {
	return uint32(self.list.length - self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(IntervalNode storage self, uint32 index) external view
	returns (uint256, int32)
    {
	uint32 _index = self.tail;
	for (uint i = 0; i < index; i++)
	    _index = self.list[_index].next;

	return (self.list[_index].endpoint, self.list[_index].core);
    }
}
