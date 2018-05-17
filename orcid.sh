#!/bin/bash


if [ ${#1} -eq 19 ]
then
    python3 -Bu contractCalls/authenticateORCID.py $1
fi
echo $1
