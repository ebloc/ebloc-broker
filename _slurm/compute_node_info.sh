# computing nodes

echo NodeName=$(hostname -s) RealMemory=$(grep "^MemTotal:" /proc/meminfo | awk '{print int($2/1024)}') Sockets=$(grep "^physical id" /proc/cpuinfo | sort -uf | wc -l) CoresPerSocket=$(grep "^siblings" /proc/cpuinfo | head -n 1 | awk '{print $3}') ThreadsPerCore=1 State=UNKNOWN
# partitions
echo PartitionName=debug  Nodes=$(hostname -s) MaxTime=INFINITE State=UP Shared=FORCE:1
