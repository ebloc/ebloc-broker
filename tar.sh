#!/bin/bash

for a in $1/*.tar.gz; do
    if [[ "$a" != $1/result-* ]] ; then
	tar -xf "$a" -C $1;
    fi
done;
