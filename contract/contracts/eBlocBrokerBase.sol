/*
  file:   eBlocBrokerBase.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
import "./Lib.sol";

contract eBlocBrokerBase {
    
    address public owner;   
    address[] providers; // A dynamically-sized array of 'address' structs 
    
    mapping(address => uint32[]) pricesSetBlockNum;
    mapping(address => Lib.Requester) requester; // Mapped address where the requester's gained Wei are collected
    mapping(address => Lib.Provider)   provider;
    
    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner {
	require(msg.sender == owner); // dev: Sender must be owner
	_ ;
    }

    /**
     * @dev Modifier to make a function callable only when given key is not zero
     */
    modifier validKey(string memory _key) {		
        require(bytes(_key).length > 0); // dev: Bad key
        _;
    }
    
    /**
     * @dev Modifier to make a function callable only when caller is registered as provider.
     */
    modifier whenProviderRegistered {
	require(provider[msg.sender].committedBlock > 0);  // dev: Not registered
	_ ;
    }

    /**
     * @dev Modifier to make a function callable only when the provider is not registered.
     */
    modifier whenProviderNotRegistered {
	require(provider[msg.sender].committedBlock == 0);  // dev: Registered
	_ ;
    }

    /**
     * @dev Modifier to make a function callable only when given timestamp is smaller than the block.timestamp(now)
     */
    modifier whenBehindNow(uint256 timestamp) {
	require(timestamp <= now);  // dev: Ahead now
	_ ;
    }

    /**
     * @dev Modifier to make a function callable only when the provider in running.
     */
    modifier whenProviderRunning {
	require(provider[msg.sender].isRunning); // dev: Provider is not running
	_ ;
    }
    
    /**
     * @dev Modifier to make a function callable only when the provider is paused.
     */
    modifier whenProviderPaused {
        require(!provider[msg.sender].isRunning); // dev: Provider is not paused
        _;
    }

    /**
     * @dev Modifier to make a function callable only when stateID is valid
     */
    modifier validJobStateCode(Lib.JobStateCodes jobStateCode) {
	/*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call */
	require(uint8(jobStateCode) > 1 && uint8(jobStateCode) <= 6);	
	_ ;
    }

    /**
     * @dev Modifier to make a function callable only when orcID is verified
     */
    modifier whenOrcidNotVerified(address _requester) {
	require(bytes(requester[_requester].orcID).length == 0); // dev: OrcID is already verified
	_ ;
    }
           
}
