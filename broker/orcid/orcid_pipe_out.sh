#!bin/bash

#sudo killall cat
while [ 1 ]
do
    cat /eBloc/fifo | xargs -I {} ~/ebloc-broker/broker/orcid/orcid.sh {}
done
