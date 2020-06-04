#!/bin/bash

mkdir -p providerResults
sudo tar czvf providerResults/varEbloc.tar.gz /var/eBlocBroker
sudo chown alper providerResults/varEbloc.tar.gz

cp -a $HOME/.eBlocBroker/endCodeAnalyse providerResults/endCodeAnalyse
cp -a $HOME/.eBlocBroker/transactions providerResults/transactions
cp $HOME/.eBlocBroker/provider.log providerResults/provider.log
