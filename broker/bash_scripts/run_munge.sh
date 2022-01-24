#!/bin/bash

sudo mkdir -p /usr/local/var/log/munge
# sudo chown munge:munge /usr/local/var/log/munge
# sudo munged --force --syslog
sudo /etc/init.d/munge start
sudo systemctl --no-pager status --full munge
