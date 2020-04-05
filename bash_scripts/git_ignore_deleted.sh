#!/bin/bash

for i in `git status | grep deleted | awk '{print $2}'`;
do
    git update-index --assume-unchanged $i;
done
