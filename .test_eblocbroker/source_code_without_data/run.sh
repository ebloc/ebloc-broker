#!/bin/bash

SLEEP_TIME=50
# clean
rm -f slurm.* completed.txt hello *.*~ helloWorld.txt
g++ helloworld.cpp -o hello
./hello
sleep $SLEEP_TIME
_date=$(LANG=en_us_88591; date)
echo "job is completed" >> completed.txt
echo "sleep ${SLEEP_TIME} seconds" >> completed.txt
echo "done" >> completed.txt
rm -f hello
