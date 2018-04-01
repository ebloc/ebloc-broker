#!/bin/bash

# pre-installation:
pip install colored
npm install --save

# Update git repository
# git fetch --all && git reset --hard origin/master

currentDir=$PWD;

if [[ ! -v COINBASE ]]; then
    echo "COINBASE is not set";
    echo "Type your cluster Ethereum Address, followed by [ENTER]:"
    read clusterID # TODO check valid Ethereum address.
    echo 'export COINBASE="$clusterID"' >>~/.profile   
elif [[ -z "$COINBASE" ]]; then
    echo "COINBASE is set to the empty string"
    echo "Type your cluster Ethereum Address, followed by [ENTER]:"
    read clusterID # TODO check valid Ethereum address.
    echo 'export COINBASE="$clusterID"' >>~/.profile   
else
    echo "COINBASE has the value: $COINBASE"
fi

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
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js         && rm $currentDir/nodePaths.js.bak
#-----------------------------------------------------
var=$(echo $currentDir | sed 's/\//\\\//g')
sudo sed -i.bak "s/^\(MailProg=\).*/\1$var\/slurmScript.sh/" /usr/local/etc/slurm.conf && sudo rm /usr/local/etc/slurm.conf.bak
grep "MailProg" /usr/local/etc/slurm.conf

# IPFS setups
sudo chown -R "$logname:$logname" ~/.ipfs/

echo -e "Note: Update the following file 'eudatPassword.txt' with your EUDAT account's password. \nBest to make sure the file is not readable or even listable for anyone but you. You achieve this with:\n 'chmod 700 eudatPassword.txt'"

echo -e "\nUpdate the following file 'miniLockPassword.txt' with your Minilock accounts password."
echo -e "Please enter your miniLock password,"
read -s PASSWORD
echo $PASSWORD > miniLockPassword.txt
chmod 700 miniLockPassword.txt
