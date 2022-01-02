#!bin/bash

# sudo killall cat
while true
do
    cat /eBloc/fifo | xargs -I {} ~/ebloc-broker/broker/orcid/orcid.sh {}
done
