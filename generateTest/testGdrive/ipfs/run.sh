#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
#SBATCH --mail-user=alper.alimoglu@gmail.com

g++ helloworld.cpp -o hello
./hello
sleep 285
#27193487932685929712749253513094955678172374969446879633700425076259478315495
echo completed 285 > completed.txt
