/*
file:   Lib.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.4.17;

library Lib {
    /* Submitted Job's information */
    struct status {
	/* Variable assigned by the cluster */
	uint8           status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint         startTime; /* Submitted job's starting universal time on the server side */	
	/* Variables assigned by the client */	
	uint          received; /* Paid amount (new owned) by the client */
	uint       blockNumber;
	//uint      priceCoreMin; /* Cluster's price for core/minute */
	uint        gasCoreMin; /* Time to run job in minutes. ex: minute + hour * 60 + day * 1440; */
	//uint priceDataTransfer;
	uint32            core; /* Requested core by the client */
	address       jobOwner; /* Address of the client (msg.sender) has been stored */
    }

    /* Registered user's information */
    struct userData {
	uint     blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */
	string   orcID; /* User's orcID */
    }

    struct clusterInfo {
	uint32 availableCoreNum;
	/* All price varaibles are defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */ 
	uint   priceCoreMin;	
	uint   priceDataTransfer; 
	uint   priceStorage; 
	uint   priceCache;
    }
    
    /* Registered cluster's information */
    struct clusterData {
	mapping(uint => clusterInfo) info;
	
	bool            isRunning; /* Flag that checks is Cluster running or not */
	uint32 clusterAddressesID; /* Cluster's ethereum address is stored */	
	uint       receivedAmount; /* Cluster's received wei price */
	uint        blockReadFrom; /* Block number when cluster is registered in order the watch cluster's event activity */

	mapping(string => status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	intervalNode receiptList; /* receiptList will be use to check either job's start and end time overlapped or not */
    }

    struct interval {
	uint   endpoint;
	int32  core; /* Job's requested core number */
	uint32 next; /* Points to next the node */
    }

    struct intervalNode {
	interval[] list; /* A dynamically-sized array of `interval` structs */
	uint32 tail; /* Tail of the linked list */
	uint32 availableCoreNum; /* Core number of the cluster */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }

    /* Invoked, when cluster calls updateCluster() function */
    function update(clusterData storage self, uint32 availableCoreNum) public
    {
	self.blockReadFrom          = block.number;	
	self.receiptList.availableCoreNum = availableCoreNum;
    }    

    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(clusterData storage self, uint32 availableCoreNum) public
    {
	self.isRunning          = true;
	self.receivedAmount     = 0;
	//self.priceDataTransfer  = priceDataTransfer;
	self.blockReadFrom      = block.number;

	intervalNode storage selfReceiptList = self.receiptList;
	selfReceiptList.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node is inserted on initialization */
	selfReceiptList.tail           = 0;	
	selfReceiptList.deletedItemNum = 0;
	selfReceiptList.availableCoreNum     = availableCoreNum;
    }

    function receiptCheck(intervalNode storage self, uint startTime, uint endTime, int32 coreNum) public
	returns (bool success)
    {
	bool     flag = false;
	uint32   addr = self.tail;
	uint32   addrTemp;
	int32    carriedSum;
	
	interval storage prevNode;     //= self.list[0];
	interval storage currentNode;  //= self.list[0];
	interval storage prevNodeTemp; //= self.list[0];

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (endTime < self.list[addr].endpoint) {
	    flag         = true;
	    prevNode     = self.list[addr];
	    currentNode  = self.list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { /* Inside while loop carriedSum is updated */
		//carriedSum += prevNode.core;
		if (endTime > currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to push the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next];
	    } while (true);
	}

	self.list.push(interval({endpoint: endTime, core: coreNum, next: addr})); /* Inserted while keeping sorted order */
	carriedSum = coreNum; /* Carried sum variable is assigned with job's given core number */
	
	if (!flag) {
	    addrTemp      = addr;	    
	    prevNode      = self.list[self.tail = uint32(self.list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(self.list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = self.list[prevNode.next]; /* Current node points index before insert operation is done */

	do {
	    if (startTime >= currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		self.list.push(interval( {endpoint: startTime, core: -1 * coreNum, next: prevNode.next}));
		prevNode.next = uint32(self.list.length - 1);
		return true;
	    }
	    carriedSum += currentNode.core;

	    /* If enters into if statement it means revert() is catch and all previous operations are reverted back */
	    if (carriedSum > int32(self.availableCoreNum)) {
		delete self.list[self.list.length-1];
		if (!flag)
		    self.tail = addrTemp;
		else
		    prevNodeTemp.next = addrTemp;

		self.deletedItemNum += 1;
		return false;
	    }
	    prevNode    = currentNode;
	    currentNode = self.list[currentNode.next];
	} while (true);

	// +-----------------------------+
	// | End: receiptCheck Algorithm |
	// +-----------------------------+
    }

    /* Used for tests */
    function getReceiptListSize(intervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length-self.deletedItemNum);
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

