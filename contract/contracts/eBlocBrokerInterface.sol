pragma solidity ^0.4.17;

interface eBlocBrokerInterface {
    
    /* Logged when the cluster calls receiptCheck function. Records the completed jobs' information under receiptCheck() method call.*/
    event LogReceipt(address indexed clusterAddress,
		     string jobKey,
		     uint index,
		     address recipient,
		     uint received,
		     uint returned,
		     uint endTime,
		     string resultIpfsHash,
		     uint8 storageID,
		     uint dataTransferIn,
		     uint dataTransferOut
		     );

    /* Records the updated jobs' information under setJobStatus() method call */
    event LogSetJob(address indexed clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint startTime
		    );
    
    /* Records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint indexed index,
		 uint8 storageID,
		 //string desc,
		 string sourceCodeHash,
		 uint32 gasDataTransferIn,
		 uint32 gasDataTransferOut,
		 uint8 cacheType,
		 uint gasStorageHour
		 );
    
    /* Eecords the registered clusters' registered information under registerCluster() method call.  (fID stands for federationCloudId) */
    event LogCluster(address indexed clusterAddress,
		     uint32 coreNumber,
		     string clusterEmail,
		     string fID,
		     string miniLockID,
		     uint priceCoreMin,
		     uint priceDataTransfer,
		     uint priceStorage,
		     uint priceCache,
		     string ipfsAddress,
		     string whisperPublicKey
		     );

    /* Records the refunded jobs' information under refund() method call */
    event LogRefund(address indexed clusterAddress,
			  string jobKey,
			  uint32 index
			  );

    /* Records the registered users' registered information under registerUser method call.*/
    event LogUser(address userAddress,
		  string userEmail,
		  string fID,
		  string miniLockID,
		  string ipfsAddress,
		  string orcID,
		  string githubUserName,
		  string whisperPublicKey
		  );
    
    event LogJobDescription(address indexed clusterAddress,
			    string jobKey,
			    string jobDesc
			    );
    
    event LogStoragePayment(address indexed clusterAddress, uint received);
}
