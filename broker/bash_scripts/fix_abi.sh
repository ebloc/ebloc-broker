#!/bin/bash

first_char=$(head -c 1 abi.json)
if  [ "$first_char" = "[" ]; then
    echo "already fixed"
    exit;
fi
sed -i 's/\"\[/\[/g' abi.json
sed -i 's/\]\"/\]/g' abi.json
sed -i 's/\\\"/\"/g' abi.json
echo "[  OK  ]"
