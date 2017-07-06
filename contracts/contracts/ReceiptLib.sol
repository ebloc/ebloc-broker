pragma solidity ^0.4.7;

library ReceiptLib {
    struct Interval {
	uint num;
	int32  core; 
	uint32 next; //Points to next node on the LinkedList.    
    }

    struct intervalNode {
	Interval[] list;
	uint32 head;
	uint32 coreLimit;
    }

    function construct(intervalNode storage self, uint32 coreLimit){ 
	self.list.push(Interval( { num: 0, core: 0, next: 0 }) ); //Dummy node
	self.list.push(Interval( { num: 0, core: 0, next: 0 }) ); //Dummy node
	self.head      = 1;
	self.coreLimit = coreLimit; 
    }

    function receiptCheck(intervalNode storage self, uint s, uint e, int32 c) returns(bool success){
	//[val, val1) s = s-1 Done.
	uint32   addr       = self.head;
	byte     flag       = '0';

	int32    carriedSum;
	Interval prevNode;
	Interval currentNode;

	if( e < self.list[addr].num ){ 	 //Addr should be updated. //find index point to push the item.
	    flag = '1';
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
	self.list.push(Interval( { num: e - 1, core: c, next: addr }) ); 

	if( flag == '0' ){ //bir yaparsan if calcar prevNode = self.head
	    carriedSum    = c;
	    prevNode      = self.list[ self.head = uint32(self.list.length - 1) ];
	}
	else
	    prevNode.next = uint32(self.list.length - 1); //araya push edilen node.
    
	currentNode = self.list[prevNode.next];//eklenmeden onceki node'dan baslar.
	while( true ) { //her kosulda kabul oluyor, s 0 da hep buyuk, counter increment yapmaya gerek yok.  
	    if( s >= currentNode.num ){ //Giving 1 block extra space with >= before it was >.
		self.list.push(Interval( { num: s, core: -1 * c, next: prevNode.next }) ); 
		prevNode.next = uint32(self.list.length - 1);	   
		return true;
	    } 	
	    carriedSum += currentNode.core;
	    if( carriedSum > int32(self.coreLimit) ) throw;
	    prevNode    = currentNode;
	    currentNode = self.list[currentNode.next]; 
	}
    }
}

  /*
  function getReceiptListSize(intervalNode storage self) constant returns(uint32) { 
    return uint32(self.list.length); 
  }
  
  function print_index(intervalNode storage self, uint32 index) constant returns(uint32, int32 ) {
    uint32 my_index = self.head;
    for ( uint i = 0; i < index; i++) { my_index = self.list[my_index].next; }
    return ( self.list[my_index].num, self.list[my_index].core );
  }
  */
