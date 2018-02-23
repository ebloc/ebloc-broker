#!/bin/bash

currentDir=$PWD;

# Folder Setup:--------------------------------------
if [ ! -d $HOME/.eBlocBroker ]; then
    mkdir $HOME/.eBlocBroker;
fi

cd     $HOME/.eBlocBroker

if [ ! -d transactions ]; then
    mkdir transactions
fi

if [ ! -d ipfsHashes ]; then
    mkdir ipfsHashes
fi

if [ ! -d endCodeAnalyse ]; then
    mkdir endCodeAnalyse 
fi

touch  $HOME/.eBlocBroker/queuedJobs.txt
touch  $HOME/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x $currentDir/slurmScript.sh
#-----------------------------------------------------

# User Name Setup:------------------------------------
lineOld="whoami";
lineNew="whoami"; #lineNew=$(logname);

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js   && rm $currentDir/nodePaths.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/checkSinfo.sh  && rm $currentDir/checkSinfo.sh.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/slurmScript.sh && rm $currentDir/slurmScript.sh.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/ipfsStat.sh    && rm $currentDir/ipfsStat.sh.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/ipfsGet.sh     && rm $currentDir/ipfsGet.sh.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak

# PATH Name Setup:------------------------------------
lineOld="EBLOCBROKER_PATH";
lineNew=$(echo $currentDir | sed 's/\//\\\//g')

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js   && rm $currentDir/nodePaths.js.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/checkSinfo.sh  && rm $currentDir/checkSinfo.sh.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/slurmScript.sh && rm $currentDir/slurmScript.sh.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/ipfsStat.sh    && rm $currentDir/ipfsStat.sh.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/ipfsGet.sh     && rm $currentDir/ipfsGet.sh.bak
#sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
#-----------------------------------------------------

# COINBASE Address Setup:-----------------------------
lineOld='0xffffffffffffffffffffffffffffffffffffffff';
lineNew='0xffffffffffffffffffffffffffffffffffffffff'; #lineNew=$(echo $COINBASE);

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/eBlocHeader.js && rm $currentDir/eBlocHeader.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/main.js        && rm $currentDir/main.js.bak
#-----------------------------------------------------
