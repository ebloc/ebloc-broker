#!/bin/sh

mkdir  ~/.eBlocBroker
cd     ~/.eBlocBroker
mkdir transactions ipfs_hashes endCodeAnalyse 

touch  ~/.eBlocBroker/queuedJobs.txt
touch  ~/.eBlocBroker/transactions/clusterOut.txt

sudo chmod +x ~/eBlocBrokerGit/slurmScript.sh

#Required after each reboot. Unneeded with the latest update.
#mkdir ~/.eBlocBroker/oc
#sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ ~/.eBlocBroker/oc
#mlck id aalimog1@binghamton.edu --save
#exfoliation econometrics revivifying obsessions transverse salving dishes
