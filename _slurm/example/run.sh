#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL

is_internet () {
    output=$(ping -c 1 -q google.com >&/dev/null; echo $?)
    if [ $output -eq 0 ]
    then
        echo "connected"
        return 0
    else
        echo "not_connected"
        return 1
    fi
}

sleep 10
hostname > completed.txt
uptime >> completed.txt
nproc >> completed.txt
firejail --allusers --noroot --net=none --disable-mnt --quiet ./run_me.sh # >> completed.txt
echo "fin" >> completed.txt
