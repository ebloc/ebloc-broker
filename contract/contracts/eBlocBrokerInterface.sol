/*
  file:   eBlocBrokerInterface.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.6.0;

interface eBlocBrokerInterface {

    // Logged when the provider calls the receiveDeposit() method. Records the completed jobs' information under receiveDeposit() method call.
    event LogProcessPayment(
        address indexed provider,
        string jobKey,
        uint32 index,
        uint32 jobID,
        address recipient,
        uint receivedWei, // Value in wei to be recevied by the provider
        uint refundedWei, // Value in wei to be refunded to the requester
        uint endTime,
        bytes32 resultIpfsHash,
        uint dataTransferIn,
        uint dataTransferOut
    );

    // Records the updated jobs' information under setJobStatus() method call
    event LogSetJob(
        address indexed provider,
        string jobKey,
        uint32 index,
        uint32 jobID,
        uint8  jobStateCodes
    );

    // Records the submitted jobs' information under submitJob() method call
    event LogJob(
        address indexed provider,
        string  jobKey,
        uint32  index,
        uint8[] cloudStorageID,
        bytes32[] sourceCodeHash,
        uint8[] cacheType,

        uint16[] core,
        uint16[] executionDuration,

        uint received,
        uint refunded
    );

    // Records the registered providers' registered information under registerProvider() method call.  (fID stands for federationCloudId)
    event LogProviderInfo(
        address indexed provider,
        string email,
        string fID,
        string miniLockID,
        string ipfsID,
        string whisperID
    );

    // Records the registered requesters' registered information under registerRequester() method call.
    event LogRequester(
        address indexed requester,
        string email,
        string fID,
        string miniLockID,
        string ipfsID,
        string githubUsername,
        string whisperID
    );

    // Records the refunded jobs' information under refund() method call
    event LogRefundRequest(
        address indexed provider,
        string jobKey,
        uint32 index,
        uint32 jobID,
        uint refundedWei
    );

    // Logs source code of the registed data files
    event LogRegisterData(
        address indexed provider,
        bytes32 registeredDataHash
    );

    event LogRegisteredDataRequestToUse(
        address indexed provider,
        bytes32 registeredDataHash
    );

    event LogJobDescription(
        address indexed provider,
        address requester,
        string jobKey,
        string jobDesc
    );

    /**
       @notice
       * For the requested job, the LogStorageDeposit() event logs the storage deposit transferred to its provider,
       * which was processed either by the submitJob() or the receiveStorageDeposit() function.
       */
    event LogStorageDeposit(
        address indexed paidAddress,
        uint payment
    );

    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );
}
