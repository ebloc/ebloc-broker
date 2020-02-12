#!/bin/bash

firstChar=$(head -c 1 abi.json)
if  [ "$firstChar" = "[" ]; then
    echo "Already fixed."
    exit;
fi


sed -i 's/\"\[/\[/g' abi.json
sed -i 's/\]\"/\]/g' abi.json
sed -i 's/\\\"/\"/g' abi.json

echo 'Fixed.'
