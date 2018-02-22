#!/bin/bash

# Folder Setup:--------------------------------------
mkdir  $HOME/.eBlocBroker
cd     $HOME/.eBlocBroker
mkdir transactions ipfs_hashes endCodeAnalyse 

touch  $HOME/.eBlocBroker/queuedJobs.txt
touch  $HOME/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x $HOME/eBlocBroker/slurmScript.sh
#-----------------------------------------------------

# Path Name Setup:------------------------------------
line_old='/alper/'
line_new='/ubuntu/'

sed -i "s%$line_old%$line_new%g" nodePaths.js
sed -i "s%$line_old%$line_new%g" checkSinfo.sh
sed -i "s%$line_old%$line_new%g" constants.py
sed -i "s%$line_old%$line_new%g" slurmScript.sh
sed -i "s%$line_old%$line_new%g" ipfsStat.sh
sed -i "s%$line_old%$line_new%g" ipfsGet.sh


line_old='0x6af0204187a93710317542d383a1b547fa42e705'
line_new='0xda1e61e853bb8d63b1426295f59cb45a34425b63' #line_new=$(echo $COINBASE)

sed -i "s%$line_old%$line_new%g" constants.py
sed -i "s%$line_old%$line_new%g" eBlocHeader.js
sed -i "s%$line_old%$line_new%g" main.js

line_old='alper'
line_new='ubuntu'

sed -i "s%$line_old%$line_new%g" constants.py
#-----------------------------------------------------
