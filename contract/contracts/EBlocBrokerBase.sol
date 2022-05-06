// SPDX-License-Identifier: MIT

/*
  file:   eBlocBrokerBase.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity >=0.7.0 <0.9.0;
import "./Lib.sol";

contract EBlocBrokerBase {
    address public owner;
    address[] registeredProviders; // A dynamically-sized array of 'address' structs
    uint32 constant ONE_HOUR_BLOCK_DURATION = 600; // ~1 hour, average block time is 6 seconds
    mapping(address => uint32) requesterCommittedBlock; // Block number when provider is registered in order the watch provider's event activity
    mapping(address => Lib.Provider) providers;
    mapping(address => uint32[]) pricesSetBlockNum;
    mapping(address => bytes32) orcID; // Mapping from address of a requester or provider to its orcID
    // mapping(string => mapping(uint32 => uint => Job) jobs;
    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(msg.sender == owner); // dev: Sender must be owner
        _;
    }

    /**
     * @dev Modifier to make a function callable only when given key is not zero
    modifier whenKeyValid(string memory _key) {
        require(bytes(_key).length > 0); // dev: Bad key
        _;
    }
    */

    /**
     * @dev Modifier to make a function callable only when caller is registered as provider.
     */
    modifier whenProviderRegistered() {
        require(providers[msg.sender].committedBlock > 0); // dev: Not registered
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the provider is not registered.
     */
    modifier whenProviderNotRegistered() {
        require(providers[msg.sender].committedBlock == 0); // dev: Registered
        _;
    }

    /**
     * @dev Modifier to make a function callable only when given timestamp is smaller than the block.timestamp.
     */
    modifier whenBehindNow(uint256 timestamp) {
        require(timestamp <= block.timestamp); // dev: Ahead block.timestamp
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the provider in running.
     */
    modifier whenProviderRunning() {
        require(providers[msg.sender].isRunning); // dev: Provider is not running
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the provider is suspended.
     */
    modifier whenProviderSuspended() {
        require(!providers[msg.sender].isRunning); // dev: Provider is not suspended
        _;
    }

    /**
     * @dev Modifier to make a function callable only when stateCode is valid
     */
    modifier validJobStateCode(Lib.JobStateCodes stateCode) {
        /*stateCode cannot be NULL, COMPLETED, REFUNDED on setJobState call */
        require(uint8(stateCode) > 1 && uint8(stateCode) < 7);
        _;
    }

    /**
     * @dev Modifier to make a function callable only when orcID is verified
     */
    modifier whenOrcidNotVerified(address _user) {
        require(orcID[_user] == 0); // dev: OrcID is already verified
        _;
    }
}
