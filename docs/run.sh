#!/bin/bash

IP=127.0.0.1
PORT=3003
/usr/local/bin/sphinx-autobuild . _build_html -H $IP --port $PORT
