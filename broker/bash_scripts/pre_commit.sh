#!/bin/bash

pre-commit run --all-files
# SKIP=mypy pre-commit run --all-files

## Files:
### ~/.isort.cfg

## mypy --ignore-missing-imports Driver.py
## black $HOME/eBlocBroker --exclude venv $HOME/eBlocBroker/docs  --line-length 80

: '
source $HOME/venv/bin/activate
echo "==> isort in process"
isort -rc $HOME/eBlocBroker

echo -e "\n=> black in process"
black . --fast --line-length 120
'
