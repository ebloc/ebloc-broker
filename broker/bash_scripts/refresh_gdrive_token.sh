#!/bin/bash

CURRENT_DIR=$PWD
cd /home/alper/git/gdrive
rm -f ~/.gdrive/token_v2.json  # delete the old token
go env -w GO111MODULE=auto
go get github.com/prasmussen/gdrive  # go install github.com/prasmussen/gdrive@latest
go build -ldflags "-w -s"
sudo cp gdrive /usr/local/bin/gdrive
./gdrive about
cd $CURRENT_DIR
