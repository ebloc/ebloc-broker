#!/bin/bash

control_c()
{
    printf goodbye
    # kill -SIGINT $(jobs -p)
    exit #$
}

trap control_c SIGINT

while true
do
    # This should be used for debugging using pdb
    ./Driver.py
    # sleep 10 &
    wait
    printf "\n"
    printf "\n"
    printf "\n"
    # loop infinitely
done
