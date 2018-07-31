#!/bin/bash                    
#                              |
# To Run:  sudo bash killall.sh|
#-------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# sudo killall ipfs

pids=$(ps aux | grep "[e]ndCode" | awk '{print $2}')
for pId in $pids
do
    sudo kill -9 $pId
done

pids=$(ps aux | grep "[s]tartCode" | awk '{print $2}')
for pId in $pids
do
    sudo kill -9 $pId
done

pids=$(ps aux | grep "[d]riverCancel" | awk '{print $2}')
for pId in $pids
do
    sudo kill -9 $pId
done

pids=$(squeue | tail -n+2 | awk '{print $1}')
for pId in $pids
do
    scancel $pids
done

pids=$(ps aux | grep "[D]river.py" | awk '{print $2}')
for pId in $pids
do
    sudo kill -9 $pId
done

echo 'DONE'
