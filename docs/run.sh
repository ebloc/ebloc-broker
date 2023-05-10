#!/bin/bash

IP=127.0.0.1
PORT=3003
sphinx-autobuild . _build_html --host $IP --port $PORT
