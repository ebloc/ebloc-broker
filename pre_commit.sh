#!/bin/bash

source $HOME/venv/bin/activate
# mypy --ignore-missing-imports Driver.py
black $HOME/eBlocBroker --exclude venv docs --fast --line-length 130
isort -rc $HOME/eBlocBroker
