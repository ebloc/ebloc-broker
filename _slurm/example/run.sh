#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

OMP_NUM_THREADS=1
sleep 10
# hostname > completed.txt
# uptime >> completed.txt
# echo "completed" >> completed.txt
