#!/bin/bash

rm -f ~/.ebloc-broker/jobs_info_0x*.out
providers=("0x29e613b04125c16db3f3613563bfdd0ba24cb629"
           "0x1926b36af775e1312fdebcc46303ecae50d945af"
           "0x4934a70ba8c1c3acfa72e809118bdd9048563a24")
for idx in "${!providers[@]}"; do
    ~/ebloc-broker/broker/_watch/watch_jobs.py ${providers[$idx]} >/dev/null &
done
# watch (ps aux | grep watch_jobs)
