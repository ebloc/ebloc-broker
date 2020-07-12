#!/bin/bash

killall python
killall python3

cd testIpfs
./cleanForNewTest.sh
./runDaemon.sh a

cd ../testNasEudat
./cleanForNewTest.sh
./runDaemon.sh a

cd ../testGdrive
./cleanForNewTest.sh
./runDaemon.sh a
