#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR

dir=$(/usr/bin/pwd)
date > completed.txt
echo "pwd="$dir >> completed.txt
uptime -p >> completed.txt
hostname >> completed.txt
echo "nproc=$(nproc)" >> completed.txt
/usr/bin/unshare -r -n ./run_me.sh
sleep 20
echo "END" >> completed.txt
