#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

g++ helloworld.cpp -o hello
./hello
sleep 180

echo completed 180 > completed.txt
