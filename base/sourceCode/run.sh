#!/bin/bash
#SBATCH -o slurm.out  # STDOUT
#SBATCH -e slurm.err  # STDERR
#SBATCH --mail-type=ALL

SLEEP_TIME=15
g++ helloworld.cpp -o hello
./hello
sleep $SLEEP_TIME

_date=$(LANG=en_us_88591; date)

cat ../data_link/2b573907a7c7075a47339969f6f3d9f7/data.txt > completed.txt
echo "job is completed. Sleep time was $SLEEP_TIME seconds." >> completed.txt
echo "date is $_date" >> completed.txt
echo "date is $_date" >> ../data_link/2b573907a7c7075a47339969f6f3d9f7/data.txt
echo "date is $_date" >> example/somedata.txt
cat example/somedata.txt > example/out.txt
echo SUCCESS >> completed.txt
