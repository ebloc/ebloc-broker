/*
file:   Lib.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;

library Lib { 
    enum StorageID {
	IPFS,          /* 0 */
	EUDAT,         /* 1 */
	IPFS_MINILOCK, /* 2 */
	GITHUB,        /* 3 */
	GDRIVE         /* 4 */
    }
    
    enum StateCodes {
	SUBMITTED,   /* 0 */
	COMPLETED,   /* 1 Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,    /* 2 Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,     /* 3 */
	RUNNING,     /* 4 */
	CANCELLED    /* 5 */	
    }

    struct DataInfo {
	uint32 price;
	bool isExist;
    }

    struct JobStorageTime {
	uint32 receivedBlock;
	uint32 cacheDuration;
    }

    struct Job {
	/* Variable assigned by the cluster */
	uint32 startTime; /* Submitted job's starting universal time on the server side */
	//uint8     status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	StateCodes status;
	
	/* Variables assigned by the client */
	uint16 core;             /* Requested core array by the client */
	uint16 executionTimeMin; /* Time to run job in minutes. ex: minute + hour * 60 + day * 1440; */
    }
    
    /* Submitted Job's information */
    struct Status {
	mapping(uint => Job) jobs;

	uint32         cacheCost;
	uint      dataTransferIn;
	uint     dataTransferOut;
	uint            received; /* Paid amount (new owned) by the client */		
	address payable jobOwner; /* Address of the client (msg.sender) has been stored */
	uint32 pricesSetBlockNum; /* When cluster is submitted cluster's most recent block number when its set or updated */
    }

    /* Registered user's information */
    struct User {
	uint32 committedBlock; /* Block number when cluster is registered in order the watch cluster's event activity */
	string orcID; /* User's orcID */
	//mapping(address => mapping(string  => bool)) isStoragePaid; /**/
    }

    struct ClusterInfo {
	uint32 availableCore; /* Core number of the cluster */
	uint32 commitmentBlockDuration;
	
	/* All the price varaibles are defined in Wei. 
	   Floating-point or fixed-point decimals have not yet been implemented in Solidity */ 
	uint32 priceCoreMin; /* Cluster's price for core per minute */
	uint32 priceDataTransfer; 
	uint32 priceStorage; 
	uint32 priceCache;	
    }
    
    /* Registered cluster's information */
    struct Cluster {
	IntervalNode receiptList; /* receiptList will be use to check either job's start and end time overlapped or not */

	mapping(string => Status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	mapping(uint => ClusterInfo) info;
	mapping(bytes32  => JobStorageTime) jobSt; /* Stored information related to job's storage time */
	mapping(address => mapping(bytes32  => uint)) receivedForStorage; /* Received payment for storage usage */
	mapping(bytes32  => DataInfo) providedData; 
	
	bool        isRunning; /* Flag that checks is Cluster running or not */
	uint         received; /* Cluster's received wei price */
	uint32 committedBlock; /* Block number when cluster is registered in order the watch cluster's event activity */
    }

    struct Interval {
	uint32 endpoint;
	int32   core; /* Job's requested core number */
	uint32  next; /* Points to next the node */
    }

    struct IntervalNode {
	Interval[] list;       /* A dynamically-sized array of interval structs */
	uint32 tail;           /* Tail of the linked list */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }    
	
    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(Cluster storage self) public
    {
	self.isRunning = true;
	self.received;
	self.committedBlock = uint32(block.number);

	IntervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(Interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
	selfReceiptList.tail;	
	selfReceiptList.deletedItemNum;
    }
			  
    function receiptCheck(IntervalNode storage self, Job storage job_, uint64 endTime_availableCore) internal
	returns (bool flag)
    {
	Interval[] storage list = self.list;
	flag = false;
	
	uint32 addr = self.tail;
	uint32 addrTemp;
	uint32 startTime = job_.startTime;
	int32  carriedSum;	
	
	Interval storage prevNode     = list[0];
	Interval storage currentNode  = list[0];
	Interval storage prevNodeTemp = list[0];

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (uint32(endTime_availableCore) < list[addr].endpoint) {
	    flag        = true;
	    prevNode    = list[addr];
	    currentNode = list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { 
		if (uint32(endTime_availableCore) > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to the pushed the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = list[currentNode.next];
	    } while (true);
	}

	list.push(Interval({endpoint: uint32(endTime_availableCore), core: int32(job_.core), next: addr})); /* Inserted while keeping sorted order */
	carriedSum = int32(job_.core); /* Carried sum variable is assigned with job's given core number */
	
	if (!flag) {
	    addrTemp      = addr;	    
	    prevNode      = list[self.tail = uint32(list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = list[prevNode.next]; /* Current node points index before insert operation is done */

	endTime_availableCore = uint32(endTime_availableCore >> 32); // availableCore is obtained and assigned
	
	do { /* Inside while loop carriedSum is updated */	    
	    if (startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		list.push(Interval({endpoint: startTime, core: -1 * int32(job_.core), next: prevNode.next}));
		prevNode.next = uint32(list.length - 1);
		return true;
	    }

	    carriedSum += currentNode.core;
	    
	    /* If enters into if statement it means revert() is catched and all the previous operations are reverted back */
	    if (carriedSum > int32(endTime_availableCore)) {			    
		delete list[list.length-1];
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
    function getReceiptListSize(IntervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length - self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(IntervalNode storage self, uint32 index) public view
	returns (uint256, int32)
    {
	uint32 myIndex = self.tail;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;

	return (self.list[myIndex].endpoint, self.list[myIndex].core);
    }
}
