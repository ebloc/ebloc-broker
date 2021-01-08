#!/bin/bash

mkdir -p providerResults
sudo tar czvf providerResults/varEbloc.tar.gz /var/ebloc-broker
sudo chown alper providerResults/varEbloc.tar.gz

cp -a $HOME/.ebloc-broker/end_code_output/ providerResults/end_code_output
cp -a $HOME/.ebloc-broker/transactions providerResults/transactions
cp $HOME/.ebloc-broker/provider.log providerResults/provider.log
