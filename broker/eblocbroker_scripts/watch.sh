#!/bin/bash

VENV=$HOME/venv
source $VENV/bin/activate
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
address="0x378181ce7b07e8dd749c6f42772574441b20e35f"
if [ $num -ge 1 ]; then
    echo "warning: watch.py is already running, count="$num
else
    rm -f ~/.ebloc-broker/watch.out
    rm -f ~/.ebloc-broker/watch_*.out
    ./watch.py $address >/dev/null &
fi
watch --color cat ~/.ebloc-broker/watch_$address.out
