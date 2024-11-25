#!/bin/bash

# source ~/venv/bin/activate
IP=127.0.0.1
PORT=8000
# sphinx-autobuild . _build_html --host $IP --port $PORT
# sphinx-autobuild . -aE _build_html
sphinx-autobuild . _build/html -b html --host 0.0.0.0 --port 8000

# https://stackoverflow.com/a/20484362/2402577
# watchmedo shell-command \
#           --patterns="*.rst" \
#           --ignore-pattern='_build/*' \
#           --recursive \
#           --command='make html'
