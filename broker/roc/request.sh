#!/bin/bash

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

publicKey="0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
name="alper"
research_title="research"
crid="QmYUBpjwEHeTr3nhyv6JLGRRSU1hnuAV63GoxorknvocE7"
email="alper@github.com"
json='{"publicKey":"'$publicKey'","crid":["'$crid'"],"cridType":"sha256","enableIPFS":false,"metadataJson":"{\"authorName\":\"'$name'\",\"researchTitle\":\"'$research_title'\",\"emailAddress\":\"'$email'\"}"}'
# json='{"publicKey":"'$publicKey'","crid":["'$crid'"],"cridType":"sha2-256","enableIPFS":false,"metadataJson":"{\"authorName\":\"'$name'\",\"researchTitle\":\"'$research_title'\",\"emailAddress\":\"'$email'\"}"}'
# echo $json
# main $json
curl 'https://certify.bloxberg.org/createBloxbergCertificate' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Origin: https://certify.bloxberg.org' \
  -H 'Referer: https://certify.bloxberg.org/' \
  -H 'api_key: 6575b56b-17ab-4cc9-a16b-d499028feee9' \
  --data-raw \
  $json \
  --compressed
