#!/bin/bash

node=$1; edge=$2
~/ebloc-broker/broker/test_setup_w/generate_w.py $node $edge
~/ebloc-broker/broker/ipfs/submit_w.py  # generate costs

wf_dir=$HOME"/test_eblocbroker/test_data/base/source_code_wf_random/"
dir="/home/alper/test_eblocbroker/workflow/${node}_${edge}"
mkdir -p $dir
cp $wf_dir/* $dir
rm -f $dir/*.pkl
