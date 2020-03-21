#!/bin/bash

./clean.sh
git add -A .

str=$1
if [ ! -z "$str" -a "$str" != " " ]; then
    git commit -m $str
else
    git commit -m "update"
fi

exit

git push
