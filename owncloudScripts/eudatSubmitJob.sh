#!/bin/bash

folderHash=$(../scripts/generateMD5sum.sh exampleFolderToShare/)
echo -e 'folderHash='$folderHash
sudo cp -a exampleFolderToShare/ oc/$folderHash
./singleFolderShare.py $folderHash

# Submit Job
clusterAddress='0x4e4a0750350796164D8DefC442a712B7557BF282'
coreNum=1
coreMinuteGas=5
jobDescription='science'
storageType=1
accountID=0

../contractCalls/submitJob.py $clusterAddress $folderHash $coreNum $coreMinuteGas $jobDescription $storageType $folderHash $accountID


