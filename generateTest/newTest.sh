#!/bin/bash

killall python

cd workingTestIpfs
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../workingTestIpfsMiniLock
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../nasEudat
bash cleanForNewTest.sh
bash runDaemon.sh a

cd ../workingGdrive
bash cleanForNewTest.sh
bash runDaemon.sh a
