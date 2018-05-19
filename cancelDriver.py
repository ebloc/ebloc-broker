#!/usr/bin/env python

import sys, os, constants, _thread

cancelledJobsReadFromPath = constants.CANCEL_JOBS_READ_FROM_FILE;
os.environ['cancelledJobsReadFromPath'] = cancelledJobsReadFromPath;

contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['contractCallPath'] = contractCallPath;


os.environ['blockReadFrom'] = os.popen('$contractCallPath/getDeployedBlockNumber.py').read().rstrip('\n');
constants.contractCall('eBlocBroker.LogCancelRefund($blockReadFrom, \'$cancelledJobsReadFromPath\')'); # Waits here until new job submitted into the cluster

print('hello')
