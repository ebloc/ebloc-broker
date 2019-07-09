pragma solidity ^0.5.7;

interface eBlocBrokerInterface {
    
    /* Logged when the cluster calls receiptCheck function. Records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address indexed clusterAddress,
		     string jobKey,
		     uint32 index,
		     uint32 jobID,
		     address recipient,
		     uint received,
		     uint returned,
		     uint endTime,
		     bytes32 resultIpfsHash,
		     uint dataTransferIn,
		     uint dataTransferOut);

    /* Records the updated jobs' information under setJobStatus() method call */
    event LogSetJob(address indexed clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint32 jobID,
		    uint startTime);
    
    /* Records the submitted jobs' information under submitJob() method call */
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint32 indexed index,
		 uint8 storageID,
		 bytes32[] sourceCodeHash,
		 uint8 cacheType,
		 uint received);
    
    /* Records the registered clusters' registered information under registerCluster() method call.  (fID stands for federationCloudId) */
    event LogClusterInfo(address indexed clusterAddress,
			 string clusterEmail,
			 string fID,
			 string miniLockID,
			 string ipfsAddress,
			 string whisperPublicKey);

    /* Records the refunded jobs' information under refund() method call */
    event LogRefund(address indexed clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint32 jobID);

    /* Records the registered users' registered information under registerUser method call.*/
    event LogUser(address userAddress,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string githubUserName,
		  string whisperPublicKey);
    
    event LogJobDescription(address indexed clusterAddress,
			    string jobKey,
			    string jobDesc);
    
    event LogStoragePayment(address indexed clusterAddress, uint received);    
}
