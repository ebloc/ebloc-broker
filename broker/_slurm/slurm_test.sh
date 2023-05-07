#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR

dir=$(/usr/bin/pwd)

log="examples/completed.txt"
{
    date
    echo "pwd="$dir
    uptime -p
    hostname
    echo "nproc=$(nproc)"
} >> $log
/usr/bin/unshare -r -n ./examples/run_me.sh
sleep 20
echo "END" >> $log
