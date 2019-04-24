/*
file:   Lib.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.4.17;
//pragma experimental ABIEncoderV2;

library Lib {
    
    enum storageID {
	IPFS,          /* 0 */
	EUDAT,         /* 1 */
	IPFS_MINILOCK, /* 2 */
	GITHUB,        /* 3 */
	GDRIVE         /* 4 */
    }
    
    enum jobStateCodes {
	NULL,        /* 0 */
	COMPLETED,   /* 1 Prevents double spending, flag to store if receiptCheck successfully completed */
	REFUNDED,    /* 2 Prevents double spending, flag to store if receiptCheck successfully refunded */
	PENDING,     /* 3 */
	RUNNING,     /* 4 */
	CANCELLED    /* 5 */	
    }

    struct Storage {
	/* Uninitialized uint variable that will be set with the block number that will be obtained when contract is constructed */
	uint      deployedBlockNumber;    
	address   owner;
	address[] clusterAddresses; /* A dynamically-sized array of `address` structs */
	mapping(address => uint[]) clusterUpdatedBlockNumber;
	mapping(address => Lib.clusterData) clusterContract;
	mapping(address => Lib.userData) userContract;
    }
    
    struct jobStorageTime {
	uint receivedBlocNumber;
	uint gasStorageBlockNum;
    }
    
    /* Submitted Job's information */
    struct status {
	/* Variable assigned by the cluster */
	uint8        status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint32    startTime; /* Submitted job's starting universal time on the server side */
	
	/* Variables assigned by the client */	
	uint     gasCoreMin; /* Time to run job in minutes. ex: minute + hour * 60 + day * 1440; */
	uint dataTransferIn;  /**/
	uint dataTransferSum; /**/
	uint32         core; /* Requested core by the client */
	 
	/* Variables obtained from eBlocBoker */
	uint    received; /* Paid amount (new owned) by the client */		
	address /*payable*/ jobOwner; /* Address of the client (msg.sender) has been stored */
	uint clusterUpdatedBlockNumber; /* When cluster is submitted cluster's most recent block number when its set or updated */
    }

    /* Registered user's information */
    struct userData {
	uint   blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
	string         orcID; /* User's orcID */

	//mapping(address => mapping(string  => bool)) isStoragePaid; /**/
    }

    struct clusterInfo {
	uint32 availableCoreNum; /* Core number of the cluster */
	/* All price varaibles are defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */ 
	uint   priceCoreMin; /* Cluster's price for core per minute */
	uint   priceDataTransfer; 
	uint   priceStorage; 
	uint   priceCache;	
    }
    
    /* Registered cluster's information */
    struct clusterData {
	intervalNode receiptList; /* receiptList will be use to check either job's start and end time overlapped or not */

	mapping(string => status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	mapping(uint => clusterInfo) info;
	mapping(bytes32  => jobStorageTime) jobSt; /*Stored information related to job's storage time*/
	mapping(address => mapping(bytes32  => uint)) receivedAmountForStorage; /**/
	
	bool            isRunning; /* Flag that checks is Cluster running or not */
	uint32 clusterAddressesID; /* Index of cluster's ethereum address is stored in clusterAddresses */	
	uint       receivedAmount; /* Cluster's received wei price */
	uint        blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
    }

    struct interval {
	uint32 endpoint;
	int32   core; /* Job's requested core number */
	uint32  next; /* Points to next the node */
    }

    struct intervalNode {
	interval[] list;       /* A dynamically-sized array of interval structs */
	uint32 tail;           /* Tail of the linked list */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }    
	
    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(clusterData storage self) public
    {
	self.isRunning      = true;
	self.receivedAmount = 0;
	self.blockReadFrom  = block.number;

	intervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
	selfReceiptList.tail             = 0;	
	selfReceiptList.deletedItemNum   = 0;
    }

    function receiptCheck(intervalNode storage self, status storage job, uint64 endTime_availableCoreNum) public	
	returns (bool flag)
    {
	interval[] storage list = self.list;
	flag = false;
	
	uint32 addr = self.tail;
	uint32 addrTemp;
	int32  carriedSum;
	
	uint32 startTime = job.startTime;
	
	interval storage prevNode     = list[0];
	interval storage currentNode  = list[0];
	interval storage prevNodeTemp = list[0];

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (uint32(endTime_availableCoreNum) < list[addr].endpoint) {
	    flag        = true;
	    prevNode    = list[addr];
	    currentNode = list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { 
		if (uint32(endTime_availableCoreNum) > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to the pushed the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = list[currentNode.next];
	    } while (true);
	}

	list.push(interval({endpoint: uint32(endTime_availableCoreNum), core: int32(job.core), next: addr})); /* Inserted while keeping sorted order */
	carriedSum = int32(job.core); /* Carried sum variable is assigned with job's given core number */
	
	if (!flag) {
	    addrTemp      = addr;	    
	    prevNode      = list[self.tail = uint32(list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = list[prevNode.next]; /* Current node points index before insert operation is done */

	endTime_availableCoreNum = uint32(endTime_availableCoreNum >> 32); // availableCoreNum is obtained and assigned
	
	do { /* Inside while loop carriedSum is updated */	    
	    if (startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		list.push(interval({endpoint: startTime, core: -1 * int32(job.core), next: prevNode.next}));
		prevNode.next = uint32(list.length - 1);
		return true;
	    }

	    //carriedSum += currentNode.core;
	    
	    /* If enters into if statement it means revert() is catch and all previous operations are reverted back */
	    if (carriedSum > int32(endTime_availableCoreNum)) {			    
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
    function getReceiptListSize(intervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length - self.deletedItemNum);
    }

    /* Used for test */
    function printIndex(intervalNode storage self, uint32 index) public view
	returns (uint256, int32)
    {
	uint32 myIndex = self.tail;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;

	return (self.list[myIndex].endpoint, self.list[myIndex].core);
    }
}
