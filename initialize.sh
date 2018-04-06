#!/bin/bash

# pre-installation:-----------------------------------------

## Python 3.5.2
# cd /usr/src
# sudo curl -O https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
# sudo tar xzf Python-3.5.2.tgz
# cd Python-3.5.2
# sudo ./configure --enable-optimizations
# sudo make altinstall
#--------------------------

## pip install
# sudo apt-get install python3-pip
# sudo pip3 install virtualenv 
# once:
# $ virtualenv -p python3 ~/.venv-py3
# each session:
# $ source ~/.venv-py3/bin/activate

# pip install typing==3.6.4 (https://github.com/ethereum/web3.py/issues/736#issuecomment-378679295)
# pip install colored
# pip install pyocclient==0.4
# pip install web3
# pip install --pre --upgrade web3

# Update git repository
# git fetch --all && git reset --hard origin/master

## gdrive install:
# go get github.com/prasmussen/gdrive
# gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
# echo 'export PATH=$PATH:$gopath/bin' >> ~/.profile
# source .profile
# gdrive about

# npm install --save
#------------------------------------------------------------

if [[ ! -v COINBASE ]]; then
    echo "COINBASE is not set";
    echo "Type your cluster Ethereum Address, followed by [ENTER]:"
    read clusterID # TODO check valid Ethereum address.
    echo 'export COINBASE="'$clusterID'"' >> $HOME/.profile   
elif [[ -z "$COINBASE" ]]; then
    echo "COINBASE is set to the empty string"
    echo "Type your cluster Ethereum Address, followed by [ENTER]:"
    read clusterID # TODO check valid Ethereum address.
    echo 'export COINBASE="'$clusterID'"' >>~/.profile   
else
    echo "COINBASE is: $COINBASE"
    check=$(node contractCalls/isAddress.js $COINBASE);
    str2="true"
    if [ "$check" != "$str2" ]; then
       echo "Ethereum address is not valid, please use a valid one.";
       exit
    fi
fi

source $HOME/.profile

currentDir=$PWD;
# Folder Setup:--------------------------------------
if [ ! -d $HOME/.eBlocBroker ]; then
    mkdir $HOME/.eBlocBroker;
fi

cd $HOME/.eBlocBroker

if [ ! -d transactions ]; then
    mkdir transactions
fi

if [ ! -d ipfsHashes ]; then
    mkdir ipfsHashes
fi

if [ ! -d endCodeAnalyse ]; then
    mkdir endCodeAnalyse 
fi

touch $HOME/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x $currentDir/slurmScript.sh
#-----------------------------------------------------

# EBLOCPATH setup
cd $currentDir
eBlocBrokerPath="$PWD"
var=$(echo $eBlocBrokerPath | sed 's/\//\\\//g')
sed -i.bak "s/^\(EBLOCPATH=\).*/\1\"$var\"/" constants.py && rm constants.py.bak

# User Name Setup:------------------------------------
lineOld="whoami";
lineNew=$(logname);

sed -i.bak "s/^\(WHOAMI=\).*/\1\"$lineNew\"/" constants.py     && rm constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js && rm $currentDir/nodePaths.js.bak

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
sudo chown -R "$logname:$logname" $HOME/.ipfs/

echo -e "Note: Update the following file 'eudatPassword.txt' with your EUDAT account's password. \nBest to make sure the file is not readable or even listable for anyone but you. You achieve this with:\n 'chmod 700 eudatPassword.txt'"

echo -e "\nUpdate the following file 'miniLockPassword.txt' with your Minilock accounts password."
echo -e "Please enter your miniLock password,"
read -s PASSWORD
echo $PASSWORD > miniLockPassword.txt
chmod 700 miniLockPassword.txt
