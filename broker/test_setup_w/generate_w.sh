#!/bin/bash

BASE=$HOME"/test_eblocbroker/test_data/base/source_code_wf_random"
job_num=10
rm -f $BASE/job*.sh
for ((i = 1 ; i <= $job_num ; i++)); do
    sleep_dur=$(echo $((15 + $RANDOM % 15)))
    cp base.sh $BASE/job$i.sh
    echo $sleep_dur
    var1="999"
    sed -i -e "s/$var1/$sleep_dur/g" $BASE/job$i.sh
done

chmod +x $BASE/job*.sh
