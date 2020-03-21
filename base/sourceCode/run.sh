#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

g++ helloworld.cpp -o hello
./hello
sleep 20

_date=$(LANG=en_us_88591; date)

cat ../data_link/5090a216e4e810d0dbf000155c708a25/data.txt > completed.txt
echo completed 20 - - - - - >> completed.txt
echo "date is $_date" >> completed.txt
echo "date is $_date" >> ../data_link/5090a216e4e810d0dbf000155c708a25/data.txt
echo COMPLETED >> completed.txt
