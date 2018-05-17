#!bin/bash 

sudo killall cat

nohup cat > /eBloc/fifo 2>&1 & 
nohup cat /eBloc/fifo | xargs -I {} bash orcid.sh {} 2>&1 &

