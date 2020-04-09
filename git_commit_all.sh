#!/bin/bash

./clean.sh
./pre_commit.sh

git add -A .
git commit
git push -f

# str=$1
#if [ ! -z "$str" -a "$str" != " " ]; then
#    git commit -m $str
#else
#    git commit -m "update"
#fi
#
