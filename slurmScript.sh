#!/bin/bash

a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $c | awk '{print $8}')
echo "Your message | $a | $b | $c //$event ." | mail -s "Message Subject" alper.alimoglu@gmail.com

scriptPath="/home/alper/eBlocBroker"; 

if [[ $c == *" Began, "* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "_" -f 1)
    arg1=$(echo $name | cut -d "_" -f 2)

    echo "JOB STARTED: $name |$arg0 $arg1 " | mail -s "Message Subject" alper.alimoglu@gmail.com
    python $scriptPath/startCode.py $arg0 $arg1     
fi

if [[ $event == *"COMPLETED"* ]]; then # Completed slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    argu0=$(echo $name | cut -d "_" -f 1)
    argu1=$(echo $name | cut -d "_" -f 2)
    argu2=$(echo $name | cut -d "_" -f 3) 
    argu3=$(echo $name | cut -d "_" -f 4) 
    
    echo "COMPLETED fileName:$name |argu0:$argu0 argu1:$argu1 argu2:$argu2 argu3:$argu3 " | mail -s "Message Subject" alper.alimoglu@gmail.com
    python $scriptPath/endCode.py $argu0 $argu1 $argu2 $argu3 $name    
fi

if [[ $event == *"TIMEOUT"* ]]; then # Timeouted slurm jobs are catched here
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Failed)')
    argu0=$(echo $name | cut -d "_" -f 1)
    argu1=$(echo $name | cut -d "_" -f 2)
    argu2=$(echo $name | cut -d "_" -f 3) 
    argu3=$(echo $name | cut -d "_" -f 4) 
    
    echo "TIMEOUT fileName:$name |argu0:$argu0 argu1:$argu1 argu2:$argu2 argu3:$argu3" | mail -s "Message Subject" alper.alimoglu@gmail.com
    python $scriptPath/endCode.py $argu0 $argu1 $argu2 $argu3 $name    
fi

if [[ $event == *" Failed, "* ]]; then # Cancelled job won't catched here

fi
