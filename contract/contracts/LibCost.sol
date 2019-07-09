/*
file:   LibCost.sol
author: Alper Alimoglu
email:  alper.alimoglu AT gmail.com
*/

pragma solidity ^0.5.7;
import "./Lib.sol";

library LibCost {
    using Lib for Lib.Cluster;

    event LogStoragePayment(address indexed clusterAddress, uint received);
	
    /* Records the submitted jobs' information under submitJob() method call.*/
    event LogJob(address indexed clusterAddress,
		 string jobKey,
		 uint32 indexed index,
		 uint8 storageID,
		 bytes32[] sourceCodeHash,
		 uint8 cacheType,
		 uint received);

    /* ------------------------------------------------------------INTERNAL_FUNCTIONS---------------------------------------------------------------- */
    
    function _logJobEvent(address _addr, string memory _key, uint32 index, uint8 storageID, bytes32[] memory sourceCodeHash, uint8 cacheType) internal {
	emit LogJob(_addr, _key, index, storageID, sourceCodeHash, cacheType, msg.value);
    }

    function _saveCoreAndCoreMin(Lib.Cluster storage cluster, string memory _key, uint16[]  memory  core, uint16[]  memory  executionTimeMin) internal
    {
	Lib.Status storage status = cluster.jobStatus[_key][cluster.jobStatus[_key].length - 1];	
	for(uint i = 0; i < core.length; i++) {
	    status.jobs[i].core    = core[i];    /* Requested core value for each job on the workflow*/
	    status.jobs[i].executionTimeMin = executionTimeMin[i]; 
	}
    }

    function _calculateComputationalCost(Lib.ClusterInfo memory info, uint16[]  memory  core, uint16[]  memory  executionTimeMin) internal
    	returns (uint sum)
    {
	uint executionTimeMinSum;
	for (uint i = 0; i < core.length; i++){
	    uint computationalCost = info.priceCoreMin * core[i] * executionTimeMin[i];
	    executionTimeMinSum += executionTimeMin[i];
	    
	    require(core[i] <= info.availableCore &&
		    computationalCost > 0         &&
		    executionTimeMinSum <= 1440 // Total execution time of the workflow should be shorter than a day 
		    );
	    
	    sum += computationalCost;
	}
	
	return sum;
    }

    function _calculateCacheCost(address payable clusterAddress,
				 Lib.Cluster storage cluster,
				 bytes32[] memory sourceCodeHash,
				 uint32[] memory dataTransferIn,
				 uint32 dataTransferOut,
				 uint32[] memory cacheTime,
				 Lib.ClusterInfo memory info) internal 
	returns (uint sum, uint32 _dataTransferIn, uint _storageCost, uint32 _cacheCost) {

	for (uint i = 0; i < sourceCodeHash.length; i++) {
	    Lib.JobStorageTime storage jobSt = cluster.jobSt[sourceCodeHash[i]];
	    uint _receivedForStorage = cluster.receivedForStorage[msg.sender][sourceCodeHash[i]];

	    if (jobSt.receivedBlock + jobSt.cacheDuration < block.number) { // Remaining time to cache is 0
		_dataTransferIn += dataTransferIn[i];

		if (cacheTime[i] > 0) { // Enter if the required time in hours to cache is not 0
		    if (_receivedForStorage > 0) {
			clusterAddress.transfer(_receivedForStorage); //storagePayment
			cluster.receivedForStorage[msg.sender][sourceCodeHash[i]] = 0;
			emit LogStoragePayment(clusterAddress, _receivedForStorage);	    
		    }
	    
		    jobSt.receivedBlock = uint32(block.number);
		    //Hour is converted into block time, 15 seconds of block time is fixed and set only one time till the storage time expires
		    jobSt.cacheDuration = cacheTime[i] * 240;

		    uint _storageCostTemp = info.priceStorage * dataTransferIn[i] * cacheTime[i];
		    cluster.receivedForStorage[msg.sender][sourceCodeHash[i]] = _storageCostTemp;		    
		    _storageCost += _storageCostTemp;
		}
		else { // Data is not cached, communication cost should be applied
		    _cacheCost += info.priceCache * dataTransferIn[i]; // cacheCost
		}
	    }
	    else { //Data is provided by the cluster with its own price
	        Lib.DataInfo storage _dataInfo = cluster.providedData[sourceCodeHash[i]];
		if (_dataInfo.isExist) 
		    _storageCost += _dataInfo.price;
	    }
	}
	
	sum += info.priceDataTransfer * (_dataTransferIn + dataTransferOut) + _storageCost + _cacheCost;

	return (sum, uint32(_dataTransferIn), uint32(_storageCost), uint32(_cacheCost));
    }
}
