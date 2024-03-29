#!/bin/bash

# Watch ongoing tests during their run time

rm -f ~/.ebloc-broker/*.yaml.lock ~/.ebloc-broker/.*.yaml.lock
providers=("0x29e613b04125c16db3f3613563bfdd0ba24cb629"
           "0x4934a70ba8c1c3acfa72e809118bdd9048563a24"
           "0xe2e146d6b456760150d78819af7d276a1223a6d4")
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo -e "==> 'watch' process is already running"
else
    rm -f ~/.ebloc-broker/watch.out ~/.ebloc-broker/watch_*.out \
       ~/ebloc-broker/broker/_watch/provider_*.txt
    for i in "${!providers[@]}"; do
        touch ~/.ebloc-broker/watch_${providers[$i]}.out
        ~/ebloc-broker/broker/_watch/watch.py "${providers[$i]}" >/dev/null &
        sleep 1
    done
fi
command watch --color head -n 28 \
        ~/.ebloc-broker/watch_${providers[0]}.out \
        ~/.ebloc-broker/watch_${providers[1]}.out \
        ~/.ebloc-broker/watch_${providers[2]}.out && clear
