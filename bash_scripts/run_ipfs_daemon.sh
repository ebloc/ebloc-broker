#!/bin/bash

~/eBlocBroker/daemons/ipfs.py
echo -e "# Sleeping for 5 seconds for ipfs to be on"
sleep 5
ipfs bootstrap list
id=$(ipfs bootstrap list | grep ip4 | head -n 1)
ipfs swarm connect $id
