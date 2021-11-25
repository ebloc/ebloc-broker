#!/bin/bash

if [ ${#1} -eq 19 ]
then
    python3 -Bu $HOME/ebloc-broker/eblocbroker/authenticate_orc_id.py $1
fi

echo $1 >> orcid.out
