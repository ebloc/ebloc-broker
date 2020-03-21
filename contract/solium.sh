#!/bin/bash

.././node_modules/.bin/prettier --write contracts/**/*.sol

# install: npm install -g ethlint --force
rm -f contracts/.#*
solium -d contracts/
