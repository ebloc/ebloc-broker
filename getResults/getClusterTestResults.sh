#!/bin/bash

mkdir -p providerResults
sudo tar czvf providerResults/varEbloc.tar.gz /var/eBlocBroker
sudo chown alper providerResults/varEbloc.tar.gz

cp -a $HOME/.eBlocBroker/end_code_output/ providerResults/end_code_output
cp -a $HOME/.eBlocBroker/transactions providerResults/transactions
cp $HOME/.eBlocBroker/provider.log providerResults/provider.log
