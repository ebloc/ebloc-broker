#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
#SBATCH --mail-user=alper.alimoglu@gmail.com

g++ helloworld.cpp -o hello
./hello
sleep 1486
#QmX8gj4f2jCRbRJbnbZgFt58uhA59neFK5A3ASS4eAmqnL
echo completed 1486 > QmX8gj4f2jCRbRJbnbZgFt58uhA59neFK5A3ASS4eAmqnL.txt
echo completed 1486 > completed.txt
