#!/bin/bash

# prc-95 username: alper.alimoglu@boun.edu.tr
mkdir -p oc/
sudo umount oc/
sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ oc/
