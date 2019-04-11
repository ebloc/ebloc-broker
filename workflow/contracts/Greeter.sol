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
}
