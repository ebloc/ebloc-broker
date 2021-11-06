#!/bin/bash

_HOME="/home/avatar_doo_avatar"  # may differ for each providerget from the file name
EMAIL="aalimog1@binghamton.edu"
VENV_PATH="${_HOME}/venv"
EBLOCBROKER_PATH="${_HOME}/ebloc-broker/broker"
LOG_FILE="${_HOME}/.ebloc-broker/slurm_script.log"
a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $c | awk '{print $8}')
msg="==> [$(date)] $a $b $c | $event"
echo $msg | mail -s "Message Subject" $EMAIL
echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-" >> $LOG_FILE
echo $msg >> $LOG_FILE
slurm_job_id=$(echo "$c" | grep -o -P '(?<=Job_id=).*(?= Name)')
if [[ $c == *" Began, "* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    msg="JOB_STARTED fname=$name\n"
    msg="${msg}start_code.py $arg0 $arg1 $slurm_job_id"
    echo $msg | mail -s "Message Subject" $EMAIL
    echo -e $msg >> $LOG_FILE
    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
        source $VENV_PATH/bin/activate
        nohup python3 -uB $EBLOCBROKER_PATH/start_code.py $arg0 $arg1 $slurm_job_id >/dev/null 2>&1
    fi
fi

if [[ $event == *"COMPLETED"* ]] || [[ $event == *"FAILED"* ]]; then
    # COMPLETED or FILLED slurm jobs are catched here
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # received_block_number
    if [[ $event == *"COMPLETED"* ]]; then
        status="COMPLETED"
    fi

    if [[ $event == *"FAILED"* ]]; then
        status="FAILED"
    fi
    msg="$status fname=$name\n"
    msg="${msg}end_code.py $arg0 $arg1 $arg2 \"$name\" $slurm_job_id"
    echo $msg | mail -s "Message Subject" $EMAIL
    echo -e $msg >> $LOG_FILE
    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
        source $VENV_PATH/bin/activate
        nohup python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $name $slurm_job_id >/dev/null 2>&1
    fi
fi

if [[ $event == *"TIMEOUT"* ]]; then
    # Timeouted slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Failed)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # received_block_number
    msg="TIMEOUT fname=$name\n"
    msg="${msg}end_code.py $arg0 $arg1 $arg2 \"$name\" $slurm_job_id"
    echo $msg | mail -s "Message Subject" $EMAIL
    echo -e $msg >> $LOG_FILE
    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
        source $VENV_PATH/bin/activate
        python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $name $slurm_job_id
    fi
fi

if [[ $event == *"CANCELLED"* ]]; then
    # Cancelled slurm jobs are catched here
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # received_block_number
    msg="CANCELLED fname=$name\n"
    msg="${msg}end_code.py $arg0 $arg1 $arg2 \"$name\" $slurm_job_id"
    echo $msg | mail -s "Message Subject" $EMAIL
    echo -e $msg >> $LOG_FILE
    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
        source $VENV_PATH/bin/activate
        nohup python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $name $slurm_job_id >/dev/null 2>&1
    fi
fi

if [[ $event == *"FAILED"* ]]; then
    # Failed slurm jobs are catched here
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)  # job_key
    arg1=$(echo $name | cut -d "*" -f 2)  # index
    arg2=$(echo $name | cut -d "*" -f 3)  # received_block_number
    msg="FAILED fname=$name\n"
    msg="${msg}end_code.py $arg0 $arg1 $arg2 \"$name\" $slurm_job_id"
    echo $msg | mail -s "Message Subject" $EMAIL
    echo -e $msg >> $LOG_FILE
    if [ "$arg0" != "$arg1" ]; then # job_key and index should not be same
        source $VENV_PATH/bin/activate
        nohup python3 -uB $EBLOCBROKER_PATH/end_code.py $arg0 $arg1 $arg2 $name $slurm_job_id >/dev/null 2>&1
    fi
fi
