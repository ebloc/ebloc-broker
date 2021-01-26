#!/bin/bash

id="1-3VQS7OC_Hs3_0TourvSlRa2vkFA3UCc"

output=$(gdrive list --query "'$id' in parents" --no-header | grep "patch_")
echo $output
patch_id=$(echo $output | grep "patch_" | awk '{print $1}')
gdrive download $patch_id
