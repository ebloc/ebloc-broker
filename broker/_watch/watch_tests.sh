#!/bin/bash

providers=("0x29e613b04125c16db3f3613563bfdd0ba24cb629"
           "0x1926b36af775e1312fdebcc46303ecae50d945af"
           "0x4934a70ba8c1c3acfa72e809118bdd9048563a24")

num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: `watch.py` is already running"
else
    rm -f ~/.ebloc-broker/watch.out ~/.ebloc-broker/watch_*.out
    for i in "${!providers[@]}"; do
        ~/ebloc-broker/broker/_watch/watch.py ${providers[$i]} >/dev/null &
    done
fi

watch --color head -n 15 \
      ~/.ebloc-broker/watch_${providers[0]}.out \
      ~/.ebloc-broker/watch_${providers[1]}.out \
      ~/.ebloc-broker/watch_${providers[2]}.out

: ' commented
cat ~/.ebloc-broker/watch_$provider_1.out
cat ~/.ebloc-broker/watch_$provider_2.out
cat ~/.ebloc-broker/watch_$provider_3.out
'
