#!/bin/bash

mkdir -p clusterResults
sudo tar czvf clusterResults/varEbloc.tar.gz /var/eBlocBroker
sudo chown alper clusterResults/varEbloc.tar.gz

cp -a ~/.eBlocBroker/endCodeAnalyse/   clusterResults/endCodeAnalyse
cp -a ~/.eBlocBroker/transactions/     clusterResults/transactions
cp    ~/.eBlocBroker/clusterDriver.out clusterResults/clusterDriver.out
