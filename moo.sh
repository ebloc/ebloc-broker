#!/bin/bash

#
# Sample shell script to demo exit code usage #
#
set -e

## find ip in the file ##
time ~/eBlocBroker/bash_scripts/git_commit_all.sh

## Did we found IP address? Use exit status of the grep command ##
if [ $? -eq 0 ]
then
  echo "Success: I found IP address in file."
  exit 0
else
  echo "Failure: I did not found IP address in file. Script failed" >&2
  exit 1
fi
