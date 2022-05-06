#!/bin/bash

sudo apt-get update -y
xargs -a <(awk '! /^ *(#|$)/' package.list) -r -- sudo apt install -yf
sudo apt autoremove -y
