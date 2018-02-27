var nodePaths   = require('../nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

coreNumber         = 128;
clusterName        = "eBloc";
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
corePriceMinuteWei = 1; 
ipfsID             = "ipfsid"; //ipfs id | grep "ID"

if(federationCloudId.length < 128 && clusterName.length < 32 && (miniLockId.length == 0 || miniLockId.length == 45))
    console.log('' + eBlocBroker.registerCluster(coreNumber, clusterName, federationCloudId, miniLockId, corePriceMinuteWei, ipfsID));
