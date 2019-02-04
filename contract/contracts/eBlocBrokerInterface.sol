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
		     uint dataTransferSum
		     );

    /* Records the updated jobs' information under setJobStatus() method call */
    event LogSetJob(address indexed clusterAddress,
		    string jobKey,
		    uint32 index,
		    uint startTime
		    );
    
    /* Records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string indexed jobKey,
		 uint indexed index,
		 uint8 storageID,
		 //string desc,
		 string sourceCodeHash,
		 uint32 gasDataTransferIn,
		 uint32 gasDataTransferOut,
		 uint8 cacheType,
		 uint gasCacheMin
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
    event LogCancelRefund(address indexed clusterAddress,
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

    function registerUser(string memory userEmail,
			  string memory fID,
			  string memory miniLockID,
                          string memory ipfsAddress,
			  string memory orcID,
                          string memory githubUserName,
			  string memory whisperPublicKey)
	public returns (bool success);

    function registerCluster(string memory clusterEmail,
                             string memory fID,
                             string memory miniLockID,
			     uint32 coreNumber,
                             uint priceCoreMin,
                             uint priceDataTransfer,
                             uint priceStorage,
			     uint priceCache,
                             string memory ipfsAddress,
                             string memory whisperPublicKey)
	public returns (bool success);

    function updateCluster(string memory clusterEmail,
			   string memory fID,
			   string memory miniLockID,
			   uint32 coreNumber,
			   uint priceCoreMin,
			   uint priceDataTransfer,
			   uint priceStorage,
			   uint priceCache,
			   string memory ipfsAddress,
			   string memory whisperPublicKey)
	public returns (bool success);

    function deregisterCluster() public returns (bool success);

    function submitJob(address clusterAddress,
		       string memory jobKey,
		       uint32 core,
		       uint32 gasCoreMin,
		       uint32 gasDataTransferIn,
		       uint32 gasDataTransferOut,
		       uint8 storageID,
		       string memory sourceCodeHash,
		       uint8 cacheType,
		       uint gasCacheMin)
	public payable /*returns (bool success)*/;

    function setJobDescription(address clusterAddress,
			       string memory jobKey,
			       string memory jobDesc)
	public returns (bool success);
    
    function setJobStatus(string memory jobKey,
			  uint32 index,
			  uint8 stateID,
			  uint startTime)
	public returns (bool success);
    
    function receiptCheck(string memory jobKey,
                          uint32 index,
                          uint32 jobRunTimeMin,
                          string memory resultIpfsHash,
                          uint8 storageID,
                          uint endTime,
                          uint dataTransferSum)
	public returns (bool success);

    function cancelRefund(address clusterAddress,
			  string memory jobKey,
			  uint32 index)
	public returns (bool);
       
    function authenticateOrcID(string memory orcID) public returns (bool success);
    
    function getJobInfo(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint8, uint32, uint, uint, uint, address);
    
    function getClusterPricesForJob(address clusterAddress, string memory jobKey, uint index) public view
	returns (uint, uint, uint, uint);

    function getClusterPricesBlockNumbers(address clusterAddress) public view
	returns (uint[] memory);

    function getClusterInfo(address clusterAddress) public view
	returns(uint, uint, uint, uint, uint, uint);

    function getUserInfo(address userAddress) public view
	returns(uint, string memory);

    function getDeployedBlockNumber() public view
	returns (uint);

    function getOwner() public view
	returns (address);

    function getJobSize(address clusterAddress, string memory jobKey) public view
	returns (uint);

    function getClusterReceivedAmount(address clusterAddress) public view
	returns (uint);
      
    function getClusterAddresses() public view
	returns (address[] memory);

    function isClusterExist(address clusterAddress) public view
	returns (bool);

    function isUserExist(address userAddress) public view
	returns (bool);
      
    function isOrcIDVerified(string memory orcID) public view
	returns (uint32);	  

    function getClusterReceiptSize(address clusterAddress) public view
	returns (uint32);

    function getClusterReceiptNode(address clusterAddress, uint32 index) public view
	returns (uint256, int32);

}
