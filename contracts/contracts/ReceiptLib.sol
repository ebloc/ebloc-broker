pragma solidity ^0.4.17;

library ReceiptLib {
    
    struct Interval {
	uint   num;
	int32  core; 
	uint32 next; //Points to next node on the LinkedList.    
    }

    struct intervalNode {
	Interval[] list;
	uint32 head;
	uint32 coreNumber;
	uint32 deletedItemNum;
    }

    function construct(intervalNode storage self, uint32 coreNumber) {
	self.list.push(Interval( { num: 0, core: 0, next: 0 }) ); //dummy node
	self.list.push(Interval( { num: 0, core: 0, next: 0 }) ); //dummy node
	self.head       = 1;
	self.coreNumber = coreNumber;
	self.deletedItemNum = 0;
    }

    function receiptCheck(intervalNode storage self, uint s, uint e, int32 c) returns(bool success) {
	//[val, val1) s = s-1 Done.
	uint32   addr       = self.head;
	bool     flag       = false; //byte flag = '0';
	
	int32    carriedSum;
	Interval prevNode;
	Interval currentNode;

	if( e < self.list[addr].num ) { 	 //Addr should be updated. //find index point to push the item.
	    flag = true; 
	    prevNode     = self.list[addr];
	    currentNode  = self.list[prevNode.next];//eklenmeden onceki node'dan baslar.
	    while( true ) { //tararken carried sumda tutulur.
		carriedSum += prevNode.core;
		if( e >= currentNode.num ){
		    addr = prevNode.next;
		    break;
		}
		prevNode    = currentNode;
		currentNode = self.list[currentNode.next]; 
	    }
	}

	uint32   addrTemp;     //alper
	Interval prevNodeTemp; //alper
	
	self.list.push(Interval( { num: e - 1, core: c, next: addr }) ); 
	if(!flag){ //bir yaparsan if calcar prevNode = self.head. 
	    addrTemp      = addr; //alper
	    carriedSum    = c;
	    prevNode      = self.list[ self.head = uint32(self.list.length - 1) ];
	}
	else{
	    addrTemp      = prevNode.next;//alper
	    prevNodeTemp  = prevNode;//alper
            prevNode.next = uint32(self.list.length - 1); //araya push edilen node.	    
	}
	currentNode = self.list[prevNode.next];//eklenmeden onceki node'dan baslar.
	    
	while( true ) { //her kosulda kabul oluyor, s 0 da hep buyuk, counter increment yapmaya gerek yok.  
	    if( s > currentNode.num ){ //Giving 1 block extra space with >= before it was >. //>= changed to >.
		self.list.push(Interval( { num: s, core: -1 * c, next: prevNode.next }) ); 
		prevNode.next = uint32(self.list.length - 1);
			
		return true;
	    } 	
	    carriedSum += currentNode.core;
	    if( carriedSum > int32(self.coreNumber) ){
	    	//throw;
		
		//alper:revert it back.------------------------------------
		delete self.list[self.list.length-1];
		if(!flag)
		    self.head = addrTemp;		
		else
		    prevNodeTemp.next = addrTemp;		
		self.deletedItemNum += 1;
		return false;//alper
		//alper:revert it back.------------------------------------	
	    }
	    prevNode    = currentNode;
	    currentNode = self.list[currentNode.next]; 
	}
    }

    //Comment out
    function getReceiptListSize(intervalNode storage self) constant returns(uint32) { 
	return uint32(self.list.length-self.deletedItemNum); 
    }
  
    function print_index(intervalNode storage self, uint32 index) constant returns(uint256, int32 ) {
	uint32 my_index = self.head;
	for ( uint i = 0; i < index; i++) { my_index = self.list[my_index].next; }
	return ( self.list[my_index].num, self.list[my_index].core );
    }
    //
}
