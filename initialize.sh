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

# sudo chmod +x $currentDir/slurmScript.sh
#-----------------------------------------------------

# Path Name Setup:------------------------------------
line_old="whoami"
line_new="whoami"

sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/nodePaths.js   #&& rm $currentDir/nodePaths.js.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/checkSinfo.sh  && rm $currentDir/checkSinfo.sh.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/slurmScript.sh && rm $currentDir/slurmScript.sh.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/ipfsStat.sh    && rm $currentDir/ipfsStat.sh.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/ipfsGet.sh     && rm $currentDir/ipfsGet.sh.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak

line_old='0xffffffffffffffffffffffffffffffffffffffff'
line_new='0xffffffffffffffffffffffffffffffffffffffff' #line_new=$(echo $COINBASE)

sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/eBlocHeader.js && rm $currentDir/eBlocHeader.js.bak
sed -i.bak 's/'$line_old'/'$line_new'/' $currentDir/main.js        && rm $currentDir/main.js.bak
#-----------------------------------------------------
