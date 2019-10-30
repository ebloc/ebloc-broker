#!/bin/bash

a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $c | awk '{print $8}')
echo "Your message | $a | $b | $c //$event ." | mail -s "Message Subject" aalimog1@binghamton.edu
VENV_PATH="/home/netlab/venv"
EBLOCBROKER_PATH="/home/netlab/eBlocBroker"

slurmJobID=$(echo "$c" | grep -o -P '(?<=Job_id=).*(?= Name)')
if [[ $c == *" Began, "* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "*" -f 1) # jobKey
    arg1=$(echo $name | cut -d "*" -f 2) # index

    echo "JOB STARTED: $name |$arg0 $arg1 slurmJobID: $slurmJobID" | mail -s "Message Subject" aalimog1@binghamton.edu

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/startCode.py $arg0 $arg1 $slurmJobID
    fi
fi

if [[ $event == *"COMPLETED"* ]]; then # Completed slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1) # jobKey
    arg1=$(echo $name | cut -d "*" -f 2) # index
    arg2=$(echo $name | cut -d "*" -f 3)
    arg3=$(echo $name | cut -d "*" -f 4)

    echo "COMPLETED fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 slurmJobID: $slurmJobID" | mail -s "Message Subject" aalimog1@binghamton.edu

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/endCode.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *"TIMEOUT"* ]]; then # Timeouted slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Failed)')
    arg0=$(echo $name | cut -d "*" -f 1) # jobKey
    arg1=$(echo $name | cut -d "*" -f 2) # index
    arg2=$(echo $name | cut -d "*" -f 3)
    arg3=$(echo $name | cut -d "*" -f 4)

    echo "TIMEOUT fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 slurmJobID: $slurmJobID" | mail -s "Message Subject" aalimog1@binghamton.edu

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/endCode.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *"CANCELLED"* ]]; then # Cancelled slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1) # jobKey
    arg1=$(echo $name | cut -d "*" -f 2) # index
    arg2=$(echo $name | cut -d "*" -f 3) # storageID
    arg3=$(echo $name | cut -d "*" -f 4) # shareToken

    echo "CANCELLED fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 slurmJobID: $slurmJobID" | mail -s "Message Subject" aalimog1@binghamton.edu
    
    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	source $VENV_PATH/bin/activate
	python3 -uB $EBLOCBROKER_PATH/endCode.py $arg0 $arg1 $arg2 $arg3 $name $slurmJobID
    fi
fi

if [[ $event == *" Failed, "* ]]; then # Cancelled job won't catched here
    :
fi
