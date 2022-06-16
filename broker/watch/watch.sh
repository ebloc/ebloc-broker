#!/bin/bash

address="0x378181ce7b07e8dd749c6f42772574441b20e35f"
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: `watch.py` is already running"
else
    rm -f ~/.ebloc-broker/watch.out ~/.ebloc-broker/watch_*.out
    ./watch.py $address >/dev/null &
fi
watch --color cat ~/.ebloc-broker/watch_$address.out
