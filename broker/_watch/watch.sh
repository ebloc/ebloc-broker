#!/bin/bash

address="0xE2e146d6B456760150d78819af7d276a1223A6d4"
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: `watch.py` is already running"
else
    rm -f ~/.ebloc-broker/watch.out ~/.ebloc-broker/watch_*.out
    ./watch.py $address >/dev/null &
fi
watch --color cat ~/.ebloc-broker/watch_$address.out
