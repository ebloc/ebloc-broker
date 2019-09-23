/*
  file:   eBlocBrokerInterface.sol
  author: Alper Alimoglu
  email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;

interface eBlocBrokerInterface {
    
    // Logged when the provider calls receiptCheck function. Records the completed jobs' information under receiptCheck() method call.
    event LogReceipt(address indexed provider,
		     string jobKey,
		     uint32 index,
		     uint32 jobID,
		     address recipient,
		     uint receivedWei, // Value in wei to be recevied by the provider
		     uint refundedWei, // Value in wei to be refunded to the requester
		     uint endTime,
		     bytes32 resultIpfsHash,
		     uint dataTransferIn,
		     uint dataTransferOut);

    // Records the updated jobs' information under setJobStatus() method call 
    event LogSetJob(address indexed provider,
		    string jobKey,
		    uint32 index,
		    uint32 jobID,
		    uint startTime);
    
    // Records the submitted jobs' information under submitJob() method call 
    event LogJob(address indexed provider,
		 string  jobKey,
		 uint32  index,
		 uint8[] storageID,
		 bytes32[] sourceCodeHash,
		 uint8 cacheType,
		 uint received);
    
    // Records the registered providers' registered information under registerProvider() method call.  (fID stands for federationCloudId) 
    event LogProviderInfo(address indexed provider,
			 string email,
			 string fID,
			 string miniLockID,
			 string ipfsAddress,
			 string whisperPublicKey);

    // Records the registered requesters' registered information under registerRequester() method call.
    event LogRequester(address indexed requester,
		       string  email,
		       string  fID,
		       string  miniLockID,
		       string  ipfsAddress,
		       string  githubUsername,
		       string  whisperPublicKey);
    
    // Records the refunded jobs' information under refund() method call
    event LogRefundRequest(address indexed provider, string jobKey, uint32 index, uint32 jobID, uint refundedWei);    
    event LogJobDescription(address indexed provider, string jobKey, string jobDesc);    
    event LogStoragePayment(address indexed provider, uint received);   
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
}
