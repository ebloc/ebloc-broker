#!/bin/bash

a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $c | awk '{print $8}')
echo "Your message | $a | $b | $c //$event ." | mail -s "Message Subject" alper.alimoglu@gmail.com
VENV_PATH="/home/alper/venv"
EBLOCBROKER_PATH="/home/alper/eBlocBroker"

jobID=$(echo "$c" | grep -o -P '(?<=Job_id=).*(?= Name)')

if [[ $c == *" Began, "* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "*" -f 1)
    arg1=$(echo $name | cut -d "*" -f 2)

    echo "JOB STARTED: $name |$arg0 $arg1 jobID: $jobID" | mail -s "Message Subject" alper.alimoglu@gmail.com

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	. $VENV_PATH/bin/activate && python3 -uB $EBLOCBROKER_PATH/startCode.py $arg0 $arg1 $jobID
    fi
fi

if [[ $event == *"COMPLETED"* ]]; then # Completed slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    arg0=$(echo $name | cut -d "*" -f 1)
    arg1=$(echo $name | cut -d "*" -f 2)
    arg2=$(echo $name | cut -d "*" -f 3)
    arg3=$(echo $name | cut -d "*" -f 4)

    echo "COMPLETED fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 jobID: $jobID" | mail -s "Message Subject" alper.alimoglu@gmail.com

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	. $VENV_PATH/bin/activate && python3 -uB $EBLOCBROKER_PATH/endCode.py $arg0 $arg1 $arg2 $arg3 $name $jobID
    fi
fi

if [[ $event == *"TIMEOUT"* ]]; then # Timeouted slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Failed)')
    arg0=$(echo $name | cut -d "*" -f 1)
    arg1=$(echo $name | cut -d "*" -f 2)
    arg2=$(echo $name | cut -d "*" -f 3)
    arg3=$(echo $name | cut -d "*" -f 4)

    echo "TIMEOUT fileName:$name |arg0:$arg0 arg1:$arg1 arg2:$arg2 arg3:$arg3 jobID: $jobID" | mail -s "Message Subject" alper.alimoglu@gmail.com

    if [ "$arg0" != "$arg1" ]; then # jobKey and index should not be same
	. $VENV_PATH/bin/activate && python3 -uB $EBLOCBROKER_PATH/endCode.py $arg0 $arg1 $arg2 $arg3 $name $jobID
    fi
fi

if [[ $event == *"CANCELLED"* ]]; then # Cancelled slurm jobs are catched here
    :
fi

if [[ $event == *" Failed, "* ]]; then # Cancelled job won't catched here
    :
fi
