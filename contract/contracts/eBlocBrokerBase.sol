/*
  file:   eBlocBrokerBase.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
import "./Lib.sol";

contract eBlocBrokerBase {
    
    address public owner;   
    address[] clusterAddresses; // A dynamically-sized array of `address` structs 
    
    mapping(address => uint32[]) pricesSetBlockNum;
    mapping(address => Lib.User) user;   
    mapping(address => Lib.Cluster) cluster;
    
    /**
     * @notice Modifier to make a function callable only when called by any account other than the owner.
     */
    modifier onlyOwner {
	require(msg.sender == owner); // sender must be owner
	_ ;
    }

    /**
     * @notice Modifier to make a function callable only when given key is not zero
     */
    modifier validKey(string memory _key) {
		
        require(bytes(_key).length > 0); // dev: Bad key
        _;
    }
    
    /**
     * @notice Modifier to make a function callable only when cluster is registered.
     */
    modifier whenClusterRegistered {
	require(cluster[msg.sender].committedBlock > 0);  // dev: Not registered
	_ ;
    }

    /**
     * @notice Modifier to make a function callable only when the cluster is not registered.
     */
    modifier whenClusterNotRegistered {
	require(cluster[msg.sender].committedBlock == 0);  // dev: Registered
	_ ;
    }

    /**
     * @notice Modifier to make a function callable only when given timestamp is smaller than the block.timestamp(now)
     */
    modifier whenBehindNow(uint256 timestamp) {
	require(timestamp <= now);  // dev: Ahead now
	_ ;
    }

    /**
     * @notice Modifier to make a function callable only when the cluster in running.
     */
    modifier whenClusterRunning {
	require(cluster[msg.sender].isRunning); // dev: Cluster is not running
	_ ;
    }
    
    /**
     * @notice Modifier to make a function callable only when the cluster is paused.
     */
    modifier whenClusterPaused {
        require(!cluster[msg.sender].isRunning); // dev: Cluster is not paused
        _;
    }

    /**
     * @notice Modifier to make a function callable only when stateID is valid
     */
    modifier validJobStateCode(Lib.JobStateCodes jobStateCode) {
	/*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call */
	require(uint8(jobStateCode) > 1 && uint8(jobStateCode) <= 6);	
	_ ;
    }

    /**
     * @notice Modifier to make a function callable only when orcID is verified
     */
    modifier whenOrcidNotVerified(address _addr) {
	require(bytes(user[_addr].orcID).length == 0); // dev: OrcID is already verified
	_ ;
    }
        
}
