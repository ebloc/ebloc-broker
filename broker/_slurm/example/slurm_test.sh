#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

dir=$(/usr/bin/pwd)
date > completed.txt
echo "pwd="$dir >> completed.txt
uptime -p >> completed.txt
hostname >> completed.txt
echo "nproc=$(nproc)" >> completed.txt
/usr/bin/unshare -r -n ./run_me.sh
sleep 10
echo "END">> completed.txt
