// SPDX-License-Identifier: MIT

/*
  file:   eBlocBrokerInterface.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity >=0.7.0 <0.9.0;

interface eBlocBrokerInterface {
    // Logged when the provider calls the receiveDeposit() method. Records the completed jobs' information under receiveDeposit() method call.
    event LogProcessPayment(
        address indexed provider,
        string jobKey,
        uint32 index,
        uint32 jobID,
        uint32 elapsedTime,
        address recipient,
        uint256 receivedGwei, // value in Gwei to be recevied by the provider
        uint256 refundedGwei, // value in Gwei to be refunded to the requester
        bytes32 resultIpfsHash,
        uint256 dataTransferIn,
        uint256 dataTransferOut
    );

    /**
     * @dev Records the updated jobs' information under setJobState*() method calls
     */
    event LogSetJob(address indexed provider, string jobKey, uint32 index, uint32 jobID, uint8 stateCodes);

    // Records the submitted jobs' information under submitJob() method call
    event LogJob(
        address indexed provider,
        address indexed owner,
        string jobKey,
        uint32 index,
        uint8[] cloudStorageID,
        bytes32[] sourceCodeHash,
        uint8[] cacheType,
        uint16[] core,
        uint16[] runTime,
        uint256 received,
        uint256 refunded
    );

    // Records the registered providers' registered information under
    // registerProvider() method call.  (fID stands for federationCloudId)
    event LogProviderInfo(
        address indexed provider,
        bytes32 indexed gpgFingerprint,
        string gmail,
        string fID,
        string ipfsID
    );

    // Records the registered requesters' registered information under
    // registerRequester() method call.
    event LogRequester(
        address indexed requester,
        bytes32 indexed gpgFingerprint,
        string gmail,
        string fID,
        string ipfsID
    );

    // Records the refunded jobs' information under refund() method call
    event LogRefundRequest(address indexed provider, string jobKey, uint32 index, uint32 jobID, uint256 refundedGwei);

    // Logs source code of the registed data files
    event LogRegisterData(address indexed provider, bytes32 registeredDataHash);

    event LogRegisteredDataRequestToUse(address indexed provider, bytes32 registeredDataHash);

    event LogDataStorageRequest(address indexed provider, address owner, bytes32 requestedHash);

    event LogJobDescription(address indexed provider, address requester, string jobKey, string jobDesc);

    /**
       @notice
       * For the requested job, the LogDepositStorage() event logs the storage
         deposit transferred to its provider, which was processed either by the
         submitJob() or the depositStorage() function.
     */
    event LogDepositStorage(address indexed paidAddress, uint256 payment);

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
}
