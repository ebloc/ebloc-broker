#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

g++ helloworld.cpp -o hello
./hello
sleep 300

echo completed 300 > completed.txt
