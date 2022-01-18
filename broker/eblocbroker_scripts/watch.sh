#!/bin/bash

VENV=$HOME/venv
source $VENV/bin/activate
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: watch.py is already running, count="$num
else
    rm ~/.ebloc-broker/watch_*.out
    ./watch.py 0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA >/dev/null &
    ./watch.py 0x765508fc8f78a465f518ae79897d0e4b249e82dc >/dev/null &
    ./watch.py 0x38cc03c7e2a7d2acce50045141633ecdcf477e9a >/dev/null &
    ./watch.py 0xeab50158e8e51de21616307a99c9604c1c453a02 >/dev/null &
fi

watch --color head -n 15 \
      ~/.ebloc-broker/watch_0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA.out \
      ~/.ebloc-broker/watch_0x765508fc8f78a465f518ae79897d0e4b249e82dc.out \
      ~/.ebloc-broker/watch_0x38cc03c7e2a7d2acce50045141633ecdcf477e9a.out \
      ~/.ebloc-broker/watch_0xeab50158e8e51de21616307a99c9604c1c453a02.out
