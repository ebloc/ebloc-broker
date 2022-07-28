#!/bin/bash

# unpin and remove all the IPFS contents from the instance
ipfs pin ls --type recursive | cut -d' ' -f1 | xargs -n1 ipfs pin rm
ipfs repo gc
