#!bin/bash 
 
cat > /eBloc/fifo & 
cat /eBloc/fifo | xargs -I {} bash orcid.sh {} 

