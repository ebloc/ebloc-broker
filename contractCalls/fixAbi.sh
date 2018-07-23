#!/bin/bash

sed -i 's/\"\[/\[/g' abi.json
sed -i 's/\]\"/\]/g' abi.json
sed -i 's/\\\"/\"/g' abi.json
