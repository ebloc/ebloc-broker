#!/bin/bash

mkdir -p providerResults
sudo tar czvf providerResults/varEbloc.tar.gz /var/eBlocBroker
sudo chown alper providerResults/varEbloc.tar.gz

cp -a ~/.eBlocBroker/endCodeAnalyse/   providerResults/endCodeAnalyse
cp -a ~/.eBlocBroker/transactions/     providerResults/transactions
cp    ~/.eBlocBroker/providerDriver.out providerResults/providerDriver.out
