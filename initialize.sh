#!/bin/bash

# pre-installation:-----------------------------------------

## npm
# wget -qO- https://deb.nodesource.com/setup_7.x | sudo bash -
# sudo npm install -g n
# sudo n latest
#--------------------------
## Python 3.5.2 # not-nessesary.
# cd /usr/src
# sudo curl -O https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
# sudo tar xzf Python-3.5.2.tgz
# cd Python-3.5.2
# sudo ./configure --enable-optimizations
# sudo make altinstall

## Python3 setup, required for all clusters! ========================================================
# python3 -m venv venv
# python3 -m venv venv
# . venv/bin/activate
# pip install web3
# pip install colored
# pip install typing==3.6.4  # (https://github.com/ethereum/web3.py/issues/736#issuecomment-378679295)
# pip install pyocclient==0.4
# pip install --pre --upgrade web3
# pip install sphinx_rtd_theme
# ==================================================================================================
## Linux Packages
# sudo apt-get install davfs2 mailutils
# sudo apt-get install python-psutil
# sudo apt-get install -y nodejs
# sudo apt-get install munge
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
# pip install sphinx_rtd_theme

# Update git repository
# git fetch --all && git reset --hard origin/master

## gdrive install:
# go get github.com/prasmussen/gdrive
# gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
# echo 'export PATH=$PATH:$gopath/bin' >> ~/.profile
# source .profile
# gdrive about

# npm install --save
#======================================================================
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
# Folder Setup:========================================================
if [ ! -d $HOME/.eBlocBroker ]; then
    mkdir -p $HOME/.eBlocBroker;
fi

cd $HOME/.eBlocBroker

if [ ! -d transactions ]; then
    mkdir -p transactions
fi

if [ ! -d ipfsHashes ]; then
    mkdir -p ipfsHashes
fi

if [ ! -d endCodeAnalyse ]; then
    mkdir -p endCodeAnalyse 
fi

touch $HOME/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x $currentDir/slurmScript.sh
#======================================================================

# EBLOCPATH setup
cd $currentDir
eBlocBrokerPath="$PWD"
var=$(echo $eBlocBrokerPath | sed 's/\//\\\//g')
sed -i.bak "s/^\(EBLOCPATH=\).*/\1\"$var\"/" constants.py && rm constants.py.bak

# User Name Setup:======================================================
lineOld="whoami";
lineNew=$(logname);

sed -i.bak "s/^\(WHOAMI=\).*/\1\"$lineNew\"/" constants.py     && rm constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' $currentDir/nodePaths.js && rm $currentDir/nodePaths.js.bak

# RPC PORT Setup:======================================================
lineOld="8545";
lineNew="8545"; # Please change if you have different RPC_PORT number

sed -i.bak "s/^\(RPC_PORT=\).*/\1$lineNew/" constants.py     && rm constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/'       nodePaths.js     && rm nodePaths.js.bak

# PATH Name Setup:===================================================
lineOld="EBLOCBROKER_PATH";
lineNew=$(echo $currentDir | sed 's/\//\\\//g')

sed -i.bak 's/'$lineOld'/'$lineNew'/' nodePaths.js   && rm nodePaths.js.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' constants.py   && rm constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/' slurmScript.sh && rm slurmScript.sh.bak
#======================================================================

# COINBASE Address Setup:==============================================
lineOld='0xffffffffffffffffffffffffffffffffffffffff';
lineNew=$(echo $COINBASE);

sed -i.bak "s/^\(CLUSTER_ID=\).*/\1\"$lineNew\"/" constants.py && rm constants.py.bak
sed -i.bak 's/'$lineOld'/'$lineNew'/'             nodePaths.js && rm nodePaths.js.bak
#======================================================================
var=$(echo $currentDir | sed 's/\//\\\//g')
sudo sed -i.bak "s/^\(MailProg=\).*/\1$var\/slurmScript.sh/" /usr/local/etc/slurm.conf && sudo rm /usr/local/etc/slurm.conf.bak
grep "MailProg" /usr/local/etc/slurm.conf

# IPFS setups
l=$(logname)
sudo chown -R "$l:$l" $HOME/.ipfs/

echo -e "Note: Update the following file 'eudatPassword.txt' with your EUDAT account's password. \nBest to make sure the file is not readable or even listable for anyone but you. You achieve this with:\n 'chmod 700 eudatPassword.txt'"

echo -e "\nUpdate the following file 'miniLockPassword.txt' with your Minilock accounts password."
echo -e "Please enter your miniLock password,"
read -s PASSWORD
echo $PASSWORD > miniLockPassword.txt
chmod 700 miniLockPassword.txt

# gdrive initialize
# rm -rf $HOME/.gdrive/
