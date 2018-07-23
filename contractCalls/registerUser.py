#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if len(sys.argv) == 8:
        account = web3.eth.accounts[int(sys.argv[1])];
        userEmail          = str(sys.argv[2]);
        federationCloudID  = str(sys.argv[3]);
        miniLockID         = str(sys.argv[4]);
        ipfsAddress        = str(sys.argv[5]);
        orcid              = str(sys.argv[6]);
        githubUserName     = str(sys.argv[7]);
    else:
        account            = web3.eth.accounts[0]; # User's Ethereum Address
        userEmail          = "alper.alimoglu@gmail.com";
        federationCloudID  = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
        miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
        ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf";
        orcid              = "0000-0001-7642-0552";
        githubUserName     = "eBloc";

    if len(federationCloudID) < 128 and len(userEmail) < 128 and len(orcid) == 19 and orcid.replace("-", "").isdigit(): #{
        tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerUser(userEmail, federationCloudID, miniLockID, ipfsAddress, orcid, githubUserName);
        print('Tx: ' + tx.hex());
#}
