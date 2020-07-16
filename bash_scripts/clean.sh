#!/bin/bash

if [ -e docs/ ]; then
    pyclean docs/
fi

rm -rf dist build */*.egg-info *.egg-info

find . -name '.DS_Store' -delete
find . -name '*.pyc' -delete
find . -name 'flycheck_*.py' -delete

find . -name 'nohup.out' -delete
find . -name '*_flymake.py' -delete
find . -name '*.*~' -delete
find . -name '*~' -delete
find . -name '\#*' -delete
find . -name '.*.*py.swo' -delete
find . -name '.*.*py.swp' -delete
find . -name 'nohup.*' -delete
find . -name "\*scratch\*" -delete

find . -name __pycache__ -type d -exec rm -rf {} +

rm -f .node-xmlhttprequest*
rm -f ./docs/solidity_lexer.pyc
rm -f ipfs.out
rm -f modified_date.txt
rm -f package-lock.json
rm -f .oc.pckl
rm -f base/meta_data.json

rm -rf docs/_build_html/
rm -rf __pycache__/
rm -rf docs/_build/

echo -e "Cleaning is completed"
