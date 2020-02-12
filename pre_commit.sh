#!/bin/bash

source $HOME/venv/bin/activate
# mypy --ignore-missing-imports Driver.py
black $HOME/eBlocBroker --exclude venv node_modules docs --fast --line-length 120
isort -rc $HOME/eBlocBroker
