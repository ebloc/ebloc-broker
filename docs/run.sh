#!/bin/bash

IP=127.0.0.1
PORT=8000
# sphinx-autobuild . _build_html --host $IP --port $PORT
sphinx-autobuild . -aE _build_html
