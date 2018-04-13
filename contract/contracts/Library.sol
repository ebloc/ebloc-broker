pragma solidity ^0.4.17;

library Library {
    
    /* Submitted Job's information */
    struct status {
	/* Variable assigned by the cluster */
	uint8           status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint         startTime; /* Submitted job's starting universal time on the server side */
	bool       receiptFlag; /* Prevents double spending, flag to store if receiptCheck successfully completed */
	
	/* Variables assigned by the client */
	uint32   coreMinuteGas; /* Time to run job in seconds. ex: minute + hour * 60 + day * 1440; */
	uint32            core; /* Requested core by the client */
	address       jobOwner; /* Address of the client (msg.sender) has been stored */
	uint   coreMinutePrice; /* Cluster's price for core/minute */
	uint          received; /* Paid amount by the client */
    }

    /* Registered cluster's information */
    struct data {
	bool               isExist; /* Flag that checks is Cluster exists or not */
	bool             isRunning; /* Flag that checks is Cluster running or not */
	uint32   memberAddressesID; /* Cluster's ethereum address is stored */
	uint       coreMinutePrice; /* Should be defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */
	uint        receivedAmount; /* Cluster's received wei price */
	uint         blockReadFrom; /* Blockn number when cluster is registered in order the watch cluster's event activity */

	mapping(string => status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	intervalNode    receiptList; /* receiptList will be use to check job's start and end time overlapped or not */
    }

    struct interval {
	uint   endpoint;
	int32  core; /* Job's requested core number */
	uint32 next; /* Points to next the node */
    }

    struct intervalNode {
	interval[] list; /* A dynamically-sized array of `interval` structs */
	uint32 tail; /* */
	uint32 coreNumber; /* Core number of the cluster */
	uint32 deletedItemNum; /* Keep track of deleted nodes */
    }

    /* Invoked, when cluster calls updateCluster */
    function update(data storage self, uint price, uint32 coreNumber) public {
	self.coreMinutePrice        = price;
	self.receiptList.coreNumber = coreNumber;
	self.blockReadFrom          = block.number;
    }    

    /* Invoked when cluster calls registerCluster() function */
    function constructCluster(data storage self, uint32 memLen, uint price, uint32 coreNumber) public {
	self.isExist           = true;
	self.isRunning         = true;
	self.receivedAmount    = 0;
	self.memberAddressesID = memLen;
	self.coreMinutePrice   = price;
	self.blockReadFrom     = block.number;

	constructReceiptList(self.receiptList, coreNumber);
    }

    function constructReceiptList(intervalNode storage self, uint32 coreNum) public
    {
	self.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node */
	//self.list.push(interval({endpoint: 0, core: 0, next: 0})); /* Dummy node */
	self.tail           = 0;
	self.coreNumber     = coreNum;
	self.deletedItemNum = 0;
    }

    function receiptCheck(intervalNode storage self, uint startTime, uint endTime, int32 coreNum) public returns (bool success)
    {
	bool     flag = false;
	uint32   addr = self.tail;
	uint32   addrTemp;
	int32    carriedSum;
	interval prevNode;
	interval currentNode;
	interval prevNodeTemp;

	// +-------------------------------+
	// | Begin: receiptCheck Algorithm |
	// +-------------------------------+

	if (endTime < self.list[addr].endpoint) {
	    flag         = true;
	    prevNode     = self.list[addr];
	    currentNode  = self.list[prevNode.next]; /* Current node points index of previous tail-node right after the insert operation */

	    do { /* Inside while loop carriedSum is updated */
		carriedSum += prevNode.core;
		if (endTime >= currentNode.endpoint) {
		    addr = prevNode.next; /* "addr" points the index to push the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next];

	    } while (true);
	}

	self.list.push(interval({endpoint: endTime - 1, core: coreNum, next: addr}));

	if (!flag) {
	    addrTemp      = addr;
	    carriedSum    = coreNum;
	    prevNode      = self.list[self.tail = uint32(self.list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
	    prevNode.next = uint32(self.list.length - 1); /* Node that pushed in-between the linked-list */
	}

	currentNode = self.list[prevNode.next]; /* Current node points index before insert operation is done */

	do {
	    if (startTime > currentNode.endpoint) { /* Covers [val, val1) s = s-1 */
		self.list.push(interval( {endpoint: startTime, core: -1*coreNum, next: prevNode.next}));
		prevNode.next = uint32(self.list.length - 1);
		return true;
	    }
	    carriedSum += currentNode.core;

	    /* If enters into if statement it means revert() is catch and all previoes operations are reverted back */
	    if (carriedSum > int32(self.coreNumber)) {
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

    /* Could be commented out, used for test */
    function getReceiptListSize(intervalNode storage self) public view
	returns (uint32)
    {
	return uint32(self.list.length-self.deletedItemNum);
    }

    /* Could be commented out, used for test */
    function printIndex(intervalNode storage self, uint32 index) public view
	returns (uint256, int32)
    {
	uint32 myIndex = self.tail;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;

	return (self.list[myIndex].endpoint, self.list[myIndex].core);
    }
}
