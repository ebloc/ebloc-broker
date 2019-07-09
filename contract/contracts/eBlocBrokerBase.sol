pragma solidity ^0.5.7;
import "./Lib.sol";

contract eBlocBrokerBase {
    uint public deployedBlock;
    
    address public owner;
    
    address[] clusterAddresses; /* A dynamically-sized array of `address` structs */
    mapping(address => uint32[]) pricesSetBlockNum;
    mapping(address => Lib.Cluster) cluster;
    mapping(address => Lib.User) user;

    modifier onlyOwner() {
	require(msg.sender == owner, "sender must be owner");
	_ ;
    }

    modifier validKey(string memory _key) {
        require(bytes(_key).length > 0, "Bad key");
        _;
    }

    modifier isClusterExists() {
	require(cluster[msg.sender].committedBlock > 0);
	_ ;
    }

    modifier isClusterRegistered() {
	require(cluster[msg.sender].committedBlock == 0, "Not registered");
	_ ;
    }

    modifier isBehindBlockTimeStamp(uint time) {
	require(time <= block.timestamp);
	_ ;
    }

    modifier isClusterRunning() {
	require(cluster[msg.sender].isRunning);
	_ ;
    }

    /**
    * @notice Modifier to make a function callable only when the cluster is paused.
    */
    modifier whenClusterPaused() {
        require(!cluster[msg.sender].isRunning, "Contract is not paused");
        _;
    }
    
    modifier checkStateID(Lib.StateCodes stateID) {
	/*stateID cannot be NULL, COMPLETED, REFUNDED on setJobStatus call */
	require(uint8(stateID) > 2 && uint8(stateID) <= 15);	
	_ ;
    }

    modifier isOrcIDverified(address _addr) {
	require(bytes(user[_addr].orcID).length == 0);
	_ ;
    }
        
}
