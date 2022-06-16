#!/bin/bash

provider_1="0x29e613b04125c16db3f3613563bfdd0ba24cb629"
provider_2="0x1926b36af775e1312fdebcc46303ecae50d945af"
provider_3="0x4934a70ba8c1c3acfa72e809118bdd9048563a24"
provider_4="0x51e2b36469cdbf58863db70cc38652da84d20c67"
num=$(ps aux | grep -E "[w]atch.py" | grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: `watch.py` is already running"
else
    rm -f ~/.ebloc-broker/watch.out ~/.ebloc-broker/watch_*.out
    ~/ebloc-broker/broker/watch/watch.py $provider_1 >/dev/null &
    ~/ebloc-broker/broker/watch/watch.py $provider_2 >/dev/null &
    ~/ebloc-broker/broker/watch/watch.py $provider_3 >/dev/null &
    ~/ebloc-broker/broker/watch/watch.py $provider_4 >/dev/null &
fi
watch --color head -n 15 \
      ~/.ebloc-broker/watch_$provider_1.out \
      ~/.ebloc-broker/watch_$provider_2.out \
      ~/.ebloc-broker/watch_$provider_3.out \
      ~/.ebloc-broker/watch_$provider_4.out

: ' commented
cat ~/.ebloc-broker/watch_$provider_1.out
cat ~/.ebloc-broker/watch_$provider_2.out
cat ~/.ebloc-broker/watch_$provider_3.out
cat ~/.ebloc-broker/watch_$provider_4.out
'
