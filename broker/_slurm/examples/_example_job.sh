#!/bin/bash
#SBATCH --job-name=example_job
#SBATCH --out="slurm-%j.out"
#SBATCH --time=01:00
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=1
#SBATCH --mail-type=ALL
##SBATCH --mem-per-cpu=1G

#mem_bytes=$(</sys/fs/cgroup/memory/slurm/uid_${SLURM_JOB_UID}/job_${SLURM_JOB_ID}/memory.limit_in_bytes)
# mem_gbytes=$(( $mem_bytes / 1024 **3 ))

echo "Starting at $(date)"
echo "Job submitted to the ${SLURM_JOB_PARTITION} partition, the default partition on ${SLURM_CLUSTER_NAME}"
echo "Job name: ${SLURM_JOB_NAME}, Job ID: ${SLURM_JOB_ID}"
echo "I have ${SLURM_CPUS_ON_NODE} CPUs on compute node $(hostname)"
# echo "  ${mem_gbytes}GiB of RAM on compute node $(hostname)"
