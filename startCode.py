#!/usr/bin/env python

import sys
import lib
import time
import subprocess

from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.set_job_status_running import set_job_status_running

w3 = getWeb3()
eBlocBroker = connectEblocBroker(w3)


def startCall(jobKey, index, slurmJobID):
    jobID = 0  # TODO: should be obtained from the user's input

    # cmd: scontrol show job slurmJobID | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
    p1 = subprocess.Popen(['scontrol', 'show', 'job', slurmJobID], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', 'StartTime'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(['grep', '-o', '-P', '(?<=StartTime=).*(?= E)'], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    date = p3.communicate()[0].decode('utf-8').strip()
    # cmd: date -d 2018-09-09T18:38:29 +"%s"
    startTime = subprocess.check_output(['date', '-d', date, "+'%s'"]).strip().decode('utf-8').replace("'", "")

    txFile = open(lib.LOG_PATH + '/transactions/' + lib.PROVIDER_ID + '.txt', 'a')
    txFile.write(lib.EBLOCPATH + "/contractCalls/set_job_status_running.py" + ' ' + jobKey + ' ' + index + ' ' + str(jobID) + ' ' + startTime + '\n')
    time.sleep(0.25)
    for attempt in range(10):
        status, tx_hash = set_job_status_running(jobKey, index, jobID, startTime, eBlocBroker, w3)
        if not status or tx_hash == "":
            txFile.write(jobKey + "_" + index + "| Try=" + str(attempt) + " " + tx_hash + '\n')
            time.sleep(15)
        else: # success
            break
    else: # we failed all the attempts - abort
        sys.exit()

    txFile.write(jobKey + '_' + index + '| tx_hash=' + tx_hash + '| set_job_status_running_started' +  ' ' + startTime + '\n')
    txFile.close()


if __name__ == '__main__':
    jobKey = sys.argv[1]
    index = sys.argv[2]
    slurmJobID = sys.argv[3]

    startCall(jobKey, index, slurmJobID)
