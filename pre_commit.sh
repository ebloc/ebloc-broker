#!/bin/bash

# Files:
## ~/.config/flake8
## ~/.isort.cfg
source $HOME/venv/bin/activate

# mypy --ignore-missing-imports Driver.py
echo "=> isort in process"
isort -rc $HOME/eBlocBroker

printf "\n=> black in process\n"
black $HOME/eBlocBroker --exclude venv docs --fast --line-length 130
