#!/bin/bash

source $HOME/venv/bin/activate

export FLASK_APP=webapp/main.py
export FLASK_DEBUG=1
python -m flask run # --port 8080
