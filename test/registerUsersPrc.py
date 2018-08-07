#!/usr/bin/python

import os

# Reqister 10 users for prc-95 for experiment purposes.

os.environ['userEmail']         = "aalimog1@binghamton.edu";
os.environ['federationCloudID'] = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
os.environ['miniLockID']        = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k";
os.environ['orcid']             = "0000-0001-7642-0552";
os.environ['ipfsAddress']       = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C";
os.environ['githubUserName']    = "eBloc";


for x in range(0, 10): #{
    os.environ['accountID'] = str(x);
    tx = os.popen('python /home/prc/eBlocBroker/contractCalls/registerUser.py $accountID $userEmail $federationCloudID $miniLockID $ipfsAddress $orcid $githubUserName 2>/dev/null').read().rstrip('\n');
    print(str(x) + ' ' + tx);
#}
