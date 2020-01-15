#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
####

g++ helloworld.cpp -o hello
./hello
sleep 15

cat  data.txt     >  completed.txt
echo completed 15... >> completed.txt

