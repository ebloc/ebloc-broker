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
    uint [] v;

    function array(uint [] variable_) {
	v = variable_;
    }

    function getMoo()
	public view returns(uint []) {
	return v;
    }

    
    function setCharacter(uint variable_) 
        external 
    {
	uint32 vari = 4294967295;
	uint32 var2 = 12;

	    
        variable = variable_;
	doo |= uint32(-1) + uint(uint(vari) << 32) + uint(uint(var2) << 64);
	doo &= 115792089237316195423570985008687907853269984665640564039439137263843715055615;
	doo |= uint(100) << 32;
 
	//doo |= uint32(100) << 32;
	
	
	
	doo = uint(uint(vari) << 64);
	//doo |= 20 << 64; 
	//doo |= 11 << 32;	
	//
	//doo |= uint32(-1);	
    }

    function getDoo()
	public view returns (int32, uint32, uint32, uint){

	uint koo = 115792089237316195423570985008687907853269984665640564039457584007913129639935 ^ 79228162495817593519834398720;
	return (int32(doo), uint32(doo >> 32), uint32(doo >> 64), koo);

    }
	    
    function getVariables() 
        public view
    returns(uint128 variable1, uint128 variable2) {
        variable1 = uint64(variable);
        variable2 = uint128(variable>>128);
    }
}
