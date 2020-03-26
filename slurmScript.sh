#!/bin/bash

HOME="/home/netlab"
VENV_PATH="${HOME}/venv"
EBLOCBROKER_PATH="${HOME}/eBlocBroker"
LOG_FILE="${HOME}/.eBlocBroker/log.txt"

a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $c | awk '{print $8}')

msg="Your message | $a | $b | $c //$event"
echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
echo $msg >> $LOG_FILE

slurmJobID=$(echo "$c" | grep -o -P '(?<=Job_id=).*(?= Name)')
if [[ $c == *" Began, "* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index

    msg="JOB STARTED: $name |$arg0 $arg1 $slurmJobID"
    echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
    echo $msg >> $LOG_FILE

    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/start_code.py $arg0 $arg1 $slurmJobID
    fi
fi

if [[ $event == *"COMPLETED"* ]] || [[ $event == *"FAILED"* ]]; then
    # COMPLETED or FILEDslurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # cloud_storage_id
    arg3=$(echo $name | cut -d "*" -f 4)  # received_block_number

    if [[ $event == *"COMPLETED"* ]]; then
        status="COMPLETED"
    fi

    if [[ $event == *"FAILED"* ]]; then
        status="FAILED"
    fi

    msg="$status fileName:$name | $arg0 $arg1 $arg2 $arg3 $name $slurmJobID"
    echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
    echo $msg >> $LOG_FILE

    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *"TIMEOUT"* ]]; then # Timeouted slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Failed)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # cloud_storage_id
    arg3=$(echo $name | cut -d "*" -f 4)  # received_block_number

    msg="TIMEOUT fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 slurmJobID: $slurmJobID"
    echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
    echo $msg >> $LOG_FILE

    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *"CANCELLED"* ]]; then # Cancelled slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # cloud_storage_id
    arg3=$(echo $name | cut -d "*" -f 4)  # received_block_number

    msg="CANCELLED fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 slurmJobID: $slurmJobID"
    echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
    echo $msg >> $LOG_FILE

    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *"FAILED"* ]]; then # Failed slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # cloud_storage_id
    arg3=$(echo $name | cut -d "*" -f 4)  # received_block_number

    msg="FAILED fileName:$name | $arg0 $arg1 $arg2 $arg3 $name $slurmJobID"
    echo $msg | mail -s "Message Subject" aalimog1@binghamton.edu
    echo $msg >> $LOG_FILE

    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi
