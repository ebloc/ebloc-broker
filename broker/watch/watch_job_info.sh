#!/bin/bash

provider_1="0x29e613b04125c16db3f3613563bfdd0ba24cb629"
provider_2="0x1926b36af775e1312fdebcc46303ecae50d945af"
provider_3="0x4934a70ba8c1c3acfa72e809118bdd9048563a24"
provider_4="0x51e2b36469cdbf58863db70cc38652da84d20c67"
rm ~/.ebloc-broker/job_infos_0x*.out
~/ebloc-broker/broker/watch/watch_jobs.py $provider_1 >/dev/null &
~/ebloc-broker/broker/watch/watch_jobs.py $provider_2 >/dev/null &
~/ebloc-broker/broker/watch/watch_jobs.py $provider_3 >/dev/null &
~/ebloc-broker/broker/watch/watch_jobs.py $provider_4 >/dev/null &

# watch (ps aux | grep watch_jobs)
