#!/bin/bash
#SBATCH -o slurm.out  # STDOUT
#SBATCH -e slurm.err  # STDERR
#SBATCH --mail-type=ALL

SLEEP_TIME=15
g++ helloworld.cpp -o hello
./hello
sleep $SLEEP_TIME

_date=$(LANG=en_us_88591; date)


DATA1_PATH="../data_link/e789b2469ff6b459d8bb2872df740634/data.txt"

cat $DATA1_PATH > completed.txt
echo "date is $_date" >> $DATA_PATH
echo "job is completed.\nSleep time was $SLEEP_TIME seconds." >> completed.txt
echo "date=$_date" >> completed.txt
echo "date=$_date" >> example/somedata.txt
cat example/somedata.txt > example/out.txt
echo SUCCESS >> completed.txt
