pragma solidity ^0.4.17;

import "./ReceiptLib.sol";

library eBlocBrokerLib {
    using ReceiptLib for ReceiptLib.intervalNode;

    /* Submitted Job's information */
    struct Status {
	/* Variable assigned by the cluster */
	uint8           status; /* Status of the submitted job {NULL, PENDING, COMPLETED, RUNNING} */
	uint         startTime; /* Submitted job's starting universal time on the server side */
	bool       receiptFlag; /* Prevents double spending, flag to store if receiptCheck successfully completed */
	
	/* Variables assigned by the client */
	uint32   coreMinuteGas; /* Time to run job in seconds. ex: minute + hour * 60 + day * 1440; */
	uint32           core;  /* Requested core by the client */
	address       jobOwner; /* Address of the client (msg.sender) has been stored */
	uint   coreMinutePrice; /* Cluster's price for core/minute */
	uint          received; /* Paid amount by the client */
    }

    /* Registered cluster's information */
    struct data {
	bool               isExist;  /* Flag that checks is Cluster exists or not */
	bool             isRunning;  /* Flag that checks is Cluster running or not */
	uint32   memberAddressesID;  /* Cluster's ethereum address is stored */
	uint       coreMinutePrice;  /* Should be defined in wei. Floating-point or fixed-point decimals have not yet been implemented in Solidity */
	uint        receivedAmount;  /* Cluster's received wei price */
	uint         blockReadFrom;  /* Blockn umber when cluster is registered in order the watch cluster's event activity */
	bytes32             ipfsId;  /* Cluster's ipfsId */
	string                name;  /* Cluster's name*/
	string    clusterMiniLockId; /* Cluster's minilock-id */
	string    federationCloudId; /* Cluster's federation cloud-id */

	mapping(string => Status[]) jobStatus; /* All submitted jobs into cluster 's Status is accessible */
	ReceiptLib.intervalNode    receiptList; /* receiptList will be use to check job's start and end time overlapped or not */
    }

    /* Invoked when cluster calls registerCluster() function */
    function construct(data storage self, string name, string fID, string clusterMiniLockId, uint32 memLen, uint price, uint32 coreNumber, bytes32 ipfsId)
	public {
	self.name              = name;
	self.federationCloudId = fID;
	self.clusterMiniLockId = clusterMiniLockId;
	self.ipfsId            = ipfsId;
	self.isExist           = true;
	self.isRunning         = true;
	self.receivedAmount    = 0;
	self.memberAddressesID = memLen;
	self.coreMinutePrice   = price;
	self.blockReadFrom     = block.number;

	self.receiptList.construct(coreNumber);
    }

    /* Invoked, when cluster calls updateCluster */
    function update(data storage self, string clusterName, string fID, string clusterMiniLockId, uint price, uint32 coreNumber, bytes32 ipfsId)
	public {
	self.name                   = clusterName;
	self.federationCloudId      = fID;
	self.clusterMiniLockId      = clusterMiniLockId;
	self.coreMinutePrice        = price;
	self.receiptList.coreNumber = coreNumber;
	self.ipfsId                 = ipfsId;
    }
}
