#!/bin/bash

./clean.sh
git add -A .

git commit

git push

# str=$1
#if [ ! -z "$str" -a "$str" != " " ]; then
#    git commit -m $str
#else
#    git commit -m "update"
#fi
#
