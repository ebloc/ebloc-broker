#!/bin/bash

while true; do
    read -p "> Do you wish to force to update eBlocBroker repository? (y/n) " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

git fetch --all && git reset --hard origin/master
