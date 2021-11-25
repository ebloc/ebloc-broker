#!/bin/bash

VENV=$HOME/venv
source $VENV/bin/activate
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: watch.py is already running, count="$num
else
    # rm watch.out
    ./watch.py >/dev/null &
fi
watch --color cat watch.out
