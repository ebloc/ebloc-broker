#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
#SBATCH --mail-user=alper.alimoglu@gmail.com

tar -xzvf NPB3.3-SER.tar.gz
rm NPB3.3-SER.tar.gz
cd NPB3.3-SER
