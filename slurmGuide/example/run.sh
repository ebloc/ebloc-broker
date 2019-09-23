#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

# data.txt => QmNeyjS4CBqR87ZuzvCwYaUSUzNkm82nXnNkr96Z1RYDV1
g++ helloworld.cpp -o hello
./hello
sleep 30

cat  data.txt      > completed.txt
echo completed 30 >> completed.txt
