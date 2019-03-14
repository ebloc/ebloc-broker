#!/bin/bash

killall python
killall python3

cd testIpfs
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../testIpfsMiniLock
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../testNasEudat
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../testGdrive
bash cleanForNewTest.sh
bash runDaemon.sh a
