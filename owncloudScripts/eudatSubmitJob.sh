#!/bin/bash

isOcMounted=$(python isOcMounted.py)

if [ "$isOcMounted" != "True" ];then
    exit
fi

## Share Zip File
if [ $# -eq 0 ]; then
    sudo chmod -R 777 exampleFolderToShare/
    sudo tar zcf exampleFolderToShare.tar.gz exampleFolderToShare
    hash=$(md5sum exampleFolderToShare.tar.gz | awk '{print $1}')
    echo -e 'hash='$hash
    mv exampleFolderToShare.tar.gz $hash.tar.gz
    sudo rsync -avhW --progress $hash.tar.gz $HOME/oc/$hash/
    rm -f $hash.tar.gz
fi

hash='1c40dae978e1aea987400b145ca48cb9'
./singleFolderShare.py $hash


## FOLDER SHARE
# hash=$(../scripts/generateMD5sum.sh exampleFolderToShare/)
# echo -e 'folderHash='$hash
# sudo rsync -avhW --progress --recursive exampleFolderToShare/ $HOME/oc/$hash/
# ./singleFolderShare.py $hash



# Submit Job
clusterAddress='0x4e4a0750350796164D8DefC442a712B7557BF282'
coreNum=1
coreMinuteGas=5
jobDescription='science'
storageType=1
accountID=0

../contractCalls/submitJob.py $clusterAddress $hash $coreNum $coreMinuteGas $jobDescription $storageType $hash $accountID


