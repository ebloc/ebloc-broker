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
    ./Driver.py
    # sleep 10 &
    wait
    printf "\n"
    printf "\n"
    printf "\n"
    # loop infinitely
done
