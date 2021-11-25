#!/bin/bash
# sudo kill -9 $(ps aux | grep -E "python.*[t]est"  | awk '{print $2}')

killall python python3

rm -f 0x*
rm -f *.*~
rm -f nohup.out
rm -f clientOutput.txt
