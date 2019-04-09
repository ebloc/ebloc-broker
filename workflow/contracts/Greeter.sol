pragma solidity ^0.4.0;

contract Greeter {
    string public greeting;
    bytes32 value;
    
    mapping(bytes32 => bytes32) workflow;

    // TODO: Populus seems to get no bytecode if `internal`
    function Greeter() public {
        greeting = 'Hello';
    }

    function setGreeting(bytes32  val) public {
	value = val;

    }

    function greet() public constant returns (bytes32) {
        return value;
    }
}
