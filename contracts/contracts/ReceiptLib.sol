pragma solidity ^0.4.17;

library ReceiptLib {
    
    struct Interval {
	uint   num;
	int32  core; 
	uint32 next; /* Points to next the node */
    }

    struct intervalNode {
	Interval[] list;
	uint32 head;
	uint32 coreNumber;
	uint32 deletedItemNum;
    }

    function construct(intervalNode storage self, uint32 coreNum)
    {
	self.list.push(Interval({num: 0, core: 0, next: 0})); /* Dummy Object */
	self.list.push(Interval({num: 0, core: 0, next: 0})); /* Dummy Object */
	self.head           = 1;
	self.coreNumber     = coreNum;
	self.deletedItemNum = 0;
    }

    function receiptCheck(intervalNode storage self, uint startPoint, uint endPoint, int32 coreNum) returns (bool success)
    { 
	bool     flag = false; 
	uint32   addr = self.head;
	uint32   addrTemp;     
	int32    carriedSum;
	Interval prevNode;
	Interval currentNode;
	Interval prevNodeTemp;
	
	// +-------------------------------+
	// | Begin: Receipt Validity check |
	// +-------------------------------+
	
	if (endPoint < self.list[addr].num) { 
	    flag         = true; 
	    prevNode     = self.list[addr];
	    currentNode  = self.list[prevNode.next]; /* Current node points index of previous head-node right after the insert operation */ 

	    do { /* Inside while loop carriedSum is updated */  
		carriedSum += prevNode.core;
		if (endPoint >= currentNode.num) {
		    addr = prevNode.next; /* "addr" points the index to push the node */
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next]; 

	    } while (true);	    
	}
	
	self.list.push(Interval({num: endPoint-1, core: coreNum, next: addr}));
	
	if (!flag) { 
	    addrTemp      = addr; 
	    carriedSum    = coreNum;
	    prevNode      = self.list[self.head = uint32(self.list.length-1)];
	} else {
	    addrTemp      = prevNode.next;
	    prevNodeTemp  = prevNode;
            prevNode.next = uint32(self.list.length - 1); /* Node that pushed in-between the linked-list */
	}
	
	currentNode = self.list[prevNode.next]; /* Current node points index before insert operation is done */ 

	do {
	    if (startPoint > currentNode.num) { /* Covers [val, val1) s = s-1 */
		self.list.push(Interval( {num: startPoint, core: -1*coreNum, next: prevNode.next})); 
		prevNode.next = uint32(self.list.length - 1);			
		return true;
	    }	   
	    carriedSum += currentNode.core;
	    
	    /* If enters into if statement it means revert() is catch and all previoes operations are reverted back */
	    if (carriedSum > int32(self.coreNumber)) {		
		delete self.list[self.list.length-1];
		if (!flag)
		    self.head = addrTemp;		
		else
		    prevNodeTemp.next = addrTemp;
		
		self.deletedItemNum += 1;
		return false;
	    }
	    prevNode    = currentNode;
	    currentNode = self.list[currentNode.next]; 
	} while (true);

	// +-----------------------------+
	// | End: Receipt Validity check |
	// +-----------------------------+		
    }

    /* Could be commented out */
    function getReceiptListSize(intervalNode storage self) constant returns (uint32)
    { 
	return uint32(self.list.length-self.deletedItemNum); 
    }

    /* Could be commented out */
    function printIndex(intervalNode storage self, uint32 index) constant returns (uint256, int32 )
    {
	uint32 myIndex = self.head;
	for (uint i = 0; i < index; i++)
	    myIndex = self.list[myIndex].next;
	
	return (self.list[myIndex].num, self.list[myIndex].core);
    }    
}
