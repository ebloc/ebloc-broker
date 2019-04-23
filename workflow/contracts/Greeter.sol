pragma solidity ^0.4.0;

contract Greeter {
    string public greeting;
    bytes32 value;
    
    mapping(bytes32 => bytes32)   workflowSingle;
    mapping(bytes32 => bytes32[]) workflowMultiple;
    
    function Greeter() public {
        greeting = 'Hello';
    }

    function setGreeting(bytes32 val) public {
	value = val;
    }

    function mapWorkflow(bytes32 val) public {
	workflowSingle[val] = val;
	
	workflowMultiple[val].push(val);
    }

    function greet() public constant returns (bytes32) {
        return value;
    }
    
    // --------
    uint variable;
    uint doo;

    function setCharacter(uint variable_) 
        external 
    {
        variable = variable_;
	doo  = uint32(-1);
	doo |= 10 << 32;
	doo |= 20 << 64; 
	doo |= 11 << 32;

	
    }

    function getDoo()
	public view returns (int32, uint32, uint32, uint){
	
	return (int32(doo), uint32(doo >> 32), uint32(doo >> 64),doo);

    }
	    
    function getVariables() 
        public view
    returns(uint128 variable1, uint128 variable2) {
        variable1 = uint64(variable);
        variable2 = uint128(variable>>128);
    }
}
