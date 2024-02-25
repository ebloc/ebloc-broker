#!/bin/bash

main () {
    # network="sepolia"
    network="bloxberg_core"
    printf "## network=$network\n"
    rm -rf build/
    brownie compile
    brownie run ResearchCertificate --network $network
    printf "## setting abi... "
    ./set_abi.sh >/dev/null 2>&1
    echo "done"
}

main | tee deploy_output.txt
