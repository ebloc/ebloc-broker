#!/bin/bash

# unpin and remove all IPFS content from my machine
ipfs pin ls --type recursive | cut -d' ' -f1 | xargs -n1 ipfs pin rm
ipfs repo gc
