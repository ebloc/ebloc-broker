#!/bin/bash
a=$(echo $0)
b=$(echo $1)
c=$(echo $2)
event=$(echo $2 | awk 'print $4')

##Update with your own path:----------
scriptPath="/home/whoami/eBlocBroker"; #Update with the  value stored under $EBLOCPATH as an open path.
##-------------------------------------

echo "Your message | $a | $b | $c | $event  " | mail -s "Message Subject" alper.alimoglu@gmail.com

if [[ $c == *"Began"* ]]; then
    name=$(echo "$c"  | grep -o -P '(?<=Name=).*(?=.sh Began)')
    arg0=$(echo $name | cut -d "_" -f 1)
    arg1=$(echo $name | cut -d "_" -f 2)

    python $scriptPath/startCode.py $arg0 $arg1 
    echo "JOB STARTED: $name |$arg0 $arg1 " | mail -s "Message Subject" alper.alimoglu@gmail.com
fi

if [[ $c == *"COMPLETED"* ]]; then #cancelled job won't catched here.
    name=$(echo "$c"   | grep -o -P '(?<=Name=).*(?=.sh Ended)')
    argu0=$(echo $name | cut -d "_" -f 1)
    argu1=$(echo $name | cut -d "_" -f 2)
    argu2=$(echo $name | cut -d "_" -f 3) 
    argu3=$(echo $name | cut -d "_" -f 4) 
    argu4=$(echo $name | cut -d "_" -f 5) 
    python $scriptPath/endCode.py $argu0 $argu1 $argu2 $argu3 $argu4 $name
    echo "COMPLETED fileName:$name |argu0:$argu0 argu1:$argu1 argu2:$argu2 argu3:$argu3 argu4:$argu4" | mail -s "Message Subject" alper.alimoglu@gmail.com
fi

if [[ $event == *" Failed, "* ]]; then #cancelled job won't catched here.

fi

if [[ $event == *"TIMEOUT"* ]]; then #cancelled job won't catched here.

fi
