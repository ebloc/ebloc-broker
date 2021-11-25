#!/bin/bash

IP=79.123.177.145
PORT=3003
sphinx-autobuild . _build_html -H $IP --port $PORT
