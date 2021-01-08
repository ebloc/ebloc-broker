#!/bin/bash

source $HOME/venv/bin/activate

cd $HOME/eBlocBroker
rm -rf $HOME/eBlocBroker/token
brownie bake token
rm $HOME/eBlocBroker/token/contracts/*
rm $HOME/eBlocBroker/token/tests/*
mv token/brownie-config.yaml token/brownie-config_.yaml

cp -a $HOME/eBlocBroker/contract/contracts/* $HOME/eBlocBroker/token/contracts
cp -a $HOME/eBlocBroker/contract/scripts/* $HOME/eBlocBroker/token/scripts
cp -a $HOME/eBlocBroker/contract/files $HOME/eBlocBroker/token
cp -a $HOME/eBlocBroker/contract/scripts/* $HOME/eBlocBroker/token/scripts
cp -a $HOME/eBlocBroker/contract/tests/* $HOME/eBlocBroker/token/tests
cp -a $HOME/eBlocBroker/contract/* $HOME/eBlocBroker/token/
