#!/bin/bash

~/ebloc-broker/broker/_daemons/ipfs.py
echo -e "# Sleeping for 7 seconds for ipfs to be on"
sleep 6
ipfs bootstrap list
id=$(ipfs bootstrap list | grep ip4 | head -n 1)
ipfs swarm connect $id
