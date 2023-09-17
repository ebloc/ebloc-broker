#!/bin/bash

_date=$(LANG=en_us_88591; date)
SLEEP_TIME=999
rm -f slurm.* hello helloWorld.txt ./*glob*~  # cleanup
fn=$(basename "$0")
echo $_date > completed_${fn}.txt
{ echo "job=${fn} is started"; echo "==> Sleep for ${SLEEP_TIME} seconds"; } >> completed_${fn}.txt
sleep $SLEEP_TIME
_date=$(LANG=en_us_88591; date)
echo $_date >> completed_${fn}.txt
echo "done" >> completed_${fn}.txt
