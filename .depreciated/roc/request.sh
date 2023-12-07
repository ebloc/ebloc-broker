#!/bin/bash

public_key="0x72C1A89fF3606aa29686Ba8d29e28dcCff06430a"
name="alper"
research_title="research"
crid="50c4860efe8f597e39a2305b05b0c299"
email="alper@github.com"
json='{"publicKey":"'$public_key'","crid":["'$crid'"],"cridType":"sha256","enableIPFS":false,"metadataJson":"{\"authorName\":\"'$name'\",\"researchTitle\":\"'$research_title'\",\"emailAddress\":\"'$email'\"}"}'

curl 'https://certify.bloxberg.org/createBloxbergCertificate' \
     -H 'Accept: application/json, text/plain, */*' \
     -H 'Content-Type: application/json;charset=UTF-8' \
     -H 'Origin: https://certify.bloxberg.org' \
     -H 'Referer: https://certify.bloxberg.org/' \
     -H 'api_key: 6575b56b-17ab-4cc9-a16b-d499028feee9' \
     --data-raw \
     $json \
     --compressed

# main () {
#     while true ; do
#         output=$(curl -s 'https://certify.bloxberg.org/createBloxbergCertificate' \
    #           -H 'Accept: application/json, text/plain, */*' \
    #           -H 'Content-Type: application/json;charset=UTF-8' \
    #           -H 'Origin: https://certify.bloxberg.org' \
    #           -H 'Referer: https://certify.bloxberg.org/' \
    #           -H 'api_key: 6575b56b-17ab-4cc9-a16b-d499028feee9' \
    #           --data-raw \
    #           $1 \
    #           --compressed)

#         if [[ $output == *"errors"* ]]; then
#           echo ""
#         else
#             echo $output
#             return
#         fi
#         sleep 2
#     done
# }

# json='{"publicKey":"'$public_key'","crid":["'$crid'"],"cridType":"sha2-256","enableIPFS":false,"metadataJson":"{\"authorName\":\"'$name'\",\"researchTitle\":\"'$research_title'\",\"emailAddress\":\"'$email'\"}"}'
# echo $json
# main $json
