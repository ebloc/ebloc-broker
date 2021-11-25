#!/bin/bash

SLEEP_DURATION=7

python ~/ebloc-broker/broker/_daemons/ipfs.py
script_output=$?
if [ "$script_output" != "100" ]; then
    echo -e "## Sleeping for "$SLEEP_DURATION" seconds for IPFS to be on"
    sleep $SLEEP_DURATION
    ipfs bootstrap list
    ipfs swarm connect $(ipfs bootstrap list | grep ip4 | head -n 1) 2>/dev/null
fi;
