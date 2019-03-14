#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
#SBATCH --mail-user=alper.alimoglu@gmail.com

g++ helloworld.cpp -o hello
./hello
sleep 247
#315557117248301929004031731795628508817120528255753996498405787853508809101713
echo completed 247 > completed.txt
