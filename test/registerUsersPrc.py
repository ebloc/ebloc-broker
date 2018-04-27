#!/usr/bin/python

import os

userEmail   = "aalimog1@binghamton.edu";
fID         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
miniLockID  = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k";
ipfsAddress = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C";

os.environ['userEmail']   = userEmail;
os.environ['fID']         = fID;
os.environ['miniLockID']  = miniLockID;
os.environ['ipfsAddress'] = ipfsAddress;

for x in range(2, 12):
    os.environ['accountID'] = str(x);
    tx = os.popen('python /home/prc/eBlocBroker/contractCalls/registerUser.py $accountID $userEmail $fID $miniLockID $ipfsAddress 2>/dev/null').read().rstrip('\n');
    print(str(x) + ' ' + tx)
