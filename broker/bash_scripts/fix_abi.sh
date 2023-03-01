#!/bin/bash

fn="abi.json"
first_char=$(head -c 1 $fn)
if  [ "$first_char" = "[" ]; then
    echo "already fixed"
    exit
fi
sed -i 's/\"\[/\[/g' $fn
sed -i 's/\]\"/\]/g' $fn
sed -i 's/\\\"/\"/g' $fn
echo "[  OK  ]"
