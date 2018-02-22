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
line_old='/alper/'
line_new='/alper/'

sed -i '' "s%$line_old%$line_new%g" $currentDir/nodePaths.js
sed -i '' "s%$line_old%$line_new%g" $currentDir/checkSinfo.sh
sed -i '' "s%$line_old%$line_new%g" $currentDir/constants.py
sed -i '' "s%$line_old%$line_new%g" $currentDir/slurmScript.sh
sed -i '' "s%$line_old%$line_new%g" $currentDir/ipfsStat.sh
sed -i '' "s%$line_old%$line_new%g" $currentDir/ipfsGet.sh


line_old='0x6af0204187a93710317542d383a1b547fa42e705'
line_new='0xda1e61e853bb8d63b1426295f59cb45a34425b63' #line_new=$(echo $COINBASE)

sed -i '' "s%$line_old%$line_new%g" $currentDir/constants.py
sed -i '' "s%$line_old%$line_new%g" $currentDir/eBlocHeader.js
sed -i '' "s%$line_old%$line_new%g" $currentDir/main.js

line_old='alper'
line_new='alper'

sed -i '' "s%$line_old%$line_new%g" $currentDir/constants.py
#-----------------------------------------------------
