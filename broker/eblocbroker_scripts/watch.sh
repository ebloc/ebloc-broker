#!/bin/bash

VENV=$HOME/venv
source $VENV/bin/activate
rm watch.out
./watch.py >/dev/null &
watch --color cat watch.out
