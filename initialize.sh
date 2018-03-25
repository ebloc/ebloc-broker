#!/bin/bash

# Update git repository
# git fetch --all && git reset --hard origin/master

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

touch  $HOME/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x $currentDir/slurmScript.sh
#-----------------------------------------------------

# User Name Setup:------------------------------------
lineOld="whoami";
lineNew=$(logname);

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js   && rm $currentDir/nodePaths.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak

# PATH Name Setup:------------------------------------
lineOld="EBLOCBROKER_PATH";
lineNew=$(echo $currentDir | sed 's/\//\\\//g')

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js   && rm $currentDir/nodePaths.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py   && rm $currentDir/constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/slurmScript.sh && rm $currentDir/slurmScript.sh.bak
#-----------------------------------------------------

# COINBASE Address Setup:-----------------------------
lineOld='0xffffffffffffffffffffffffffffffffffffffff';
lineNew=$(echo $COINBASE);

sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/constants.py         && rm $currentDir/constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/eBlocBrokerHeader.js && rm $currentDir/eBlocBrokerHeader.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/main.js              && rm $currentDir/main.js.bak
#-----------------------------------------------------
var=$(echo $currentDir | sed 's/\//\\\//g')
sudo sed -i.bak "s/^\(MailProg=\).*/\1$var\/slurmScript.sh/" /usr/local/etc/slurm.conf && sudo rm /usr/local/etc/slurm.conf.bak
grep "MailProg" /usr/local/etc/slurm.conf

cd $currentDir/
npm install --save

echo -e "Note: Update the following file 'eudatPassword.txt' with your EUDAT account's password. \nBest to make sure the file is not readable or even listable for anyone but you. You achieve this with:\n 'chmod 700 eudatPassword.txt'"

echo -e "\nNote: Update the following file 'miniLockPassword.txt' with your Minilock account's password. \nBest to make sure the file is not readable or even listable for anyone but you. You achieve this with:\n 'chmod 700 miniLockPassword.txt'"

# IPFS setups
chown -R "$logname:$logname" ~/.ipfs/

# pip install
sudo pip install colored
