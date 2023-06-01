#!/bin/bash

sbatch job0.sh
sbatch --dependency=afterok:28 job1.sh
sbatch --dependency=afterok:28 job2.sh
sbatch --dependency=afterok:5:71 job3.sh
