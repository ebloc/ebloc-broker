#!/bin/bash

#gzip -d DAS2-fs0-2003-1.swf.gz
name=DAS2-fs1-2003-1.swf
awk '{print $2 " " $2+$4 " " $5 " " $2+$4-$2}' $name > ../test_$name
