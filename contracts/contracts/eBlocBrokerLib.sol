pragma solidity ^0.4.17;
import "./ReceiptLib.sol";

library eBlocBrokerLib {
    using ReceiptLib for ReceiptLib.intervalNode;

    struct Status {
	/*Variable updated by the cluster */
	uint8           status;
	uint32           core;
	uint    startTimeStamp;
	uint          received;
	uint   coreMinutePrice; /* Should be defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */

	/* Variables updated by the client */
	uint32   coreMinuteGas;
	address       jobOwner;
	bool       receiptFlag;
    }

    struct data {
	bool               isExist;
	bool             isRunning;
	uint32   memberAddressesID;
	uint       coreMinutePrice; /* Should be defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */
	uint        receivedAmount;
	uint         blockReadFrom;
	bytes32             ipfsId;
	string                name;
	string    clusterMiniLockId;
	string    federationCloudId;

	mapping(string => Status[])    jobStatus; 
	ReceiptLib.intervalNode      receiptList;
    }

    function construct(data storage self, string name, string fID, string clusterMiniLockId, uint32 memLen, uint price, uint32 coreNumber, bytes32 ipfsId){
	self.name              = name; 
	self.federationCloudId = fID; 
	self.clusterMiniLockId = clusterMiniLockId;
	self.ipfsId            = ipfsId;
	self.isExist           = true;
	self.isRunning         = true;
	self.receivedAmount    = 0;
	self.memberAddressesID = memLen;
	self.coreMinutePrice   = price; /* currency is wei */
	self.blockReadFrom     = block.number; /* Cluster's starting block number in order to check event */
	self.receiptList.construct(coreNumber);
    }

    function update(data storage self, string clusterName, string fID, string clusterMiniLockId, uint price, uint32 coreNumber, bytes32 ipfsId) {
	self.name                   = clusterName;
	self.federationCloudId      = fID;
	self.clusterMiniLockId      = clusterMiniLockId;
	self.coreMinutePrice        = price; /* currency is wei) */
	self.receiptList.coreNumber = coreNumber;
	self.ipfsId                 = ipfsId;
    } 
}
