#!/bin/bash

# netlab <cluster> username: aalimog1@binghamton.edu == dgxPM-HfMoQ-tFTER-mpEmg-dPWMi
# prc-95 <user>    username: alper.alimoglu@boun.edu.tr == k6zik-sMQAL-TgXDA-pmWeg-7pzcz
mkdir -p /oc
sudo umount /oc
sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc
sudo chown $(whoami) -R /oc
