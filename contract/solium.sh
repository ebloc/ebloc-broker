#!/bin/bash

# https://github.com/duaraghav8/solium-plugin-security
# install:
# npm install -g ethlint --force
# npm install -g --save-dev prettier prettier-plugin-solidity

prettier --write contracts/**/*.sol --config .prettierrce | grep -v "No parser could be inferred for file"
echo "prettier... done"
rm -f contracts/.#*
solium --config contracts/.soliumrc.json -d contracts/ --no-soliumignore | \
    grep -v "unexpected token" | grep -v "✖" | head -n -2
