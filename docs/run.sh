#!/bin/bash

# source ~/venv/bin/activate
IP=127.0.0.1
PORT=8000
# sphinx-autobuild . _build_html --host $IP --port $PORT
sphinx-autobuild . -aE _build_html

# https://stackoverflow.com/a/20484362/2402577
# watchmedo shell-command \
#           --patterns="*.rst" \
#           --ignore-pattern='_build/*' \
#           --recursive \
#           --command='make html'
