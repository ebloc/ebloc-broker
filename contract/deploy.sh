#!/bin/bash

main () {
    output=$(cat ~/ebloc-broker/contract/contracts/*.sol | tr '[:upper:]' '[:lower:]' | grep 'fixme\|uncomment\|todo')
    if [ -n "$output" ]; then
        printf "#> something is wrong:\n${output}"
        return
    else
        network="bloxberg"  # "eblocpoa"
        echo -e "## network="$network
        rm -rf build/
        brownie compile
        brownie run eBlocBroker --network $network
        printf "## setting abi... "
        ./set_abi.sh  >/dev/null 2>&1
        echo "done"
    fi
}

main | tee deploy_output.txt
