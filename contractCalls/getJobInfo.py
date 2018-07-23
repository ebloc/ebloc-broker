#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if(len(sys.argv) == 4):
        clusterAddress = str(sys.argv[1]);
        jobKey         = str(sys.argv[2]);
        index          = int(sys.argv[3]);
    else:
        clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
        jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=117649886378445811229351254502963812811";
        index          = 3;
        #jobKey          = "QmTXyUrHxkf2m85W6Sy6VAMBuZyZAuSDQAbjSgDcLLnEdW";
        #index           = 4;
    clusterAddress = web3.toChecksumAddress(clusterAddress);
    print(eBlocBroker.call().getJobInfo(clusterAddress, jobKey, index));
    # print(eBlocBroker.functions.getJobInfo(clusterAddress, jobKey, index).call());
#}
