#!/bin/bash

sudo pkill -f "Driver.py"

pids=$(ps aux | grep "[e]ndCode" | awk '{print $2}')
for word in $pids
do
    sudo kill -9 $word
done


