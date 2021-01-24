#!/bin/bash

# if [ -e docs/ ]; then
#     pyclean docs/
# fi

GREEN='\033[0;32m'
NC='\033[0m' # No Color

pyclean () {
    find . | grep -E "(.mypy_cache|.pytest_cache|__pycache__|\.pyc|\.pyo$)" | \
        xargs rm -rf &>/dev/null
}

# rm -rf dist build */*.egg-info *.egg-info

find . -name '.DS_Store' -delete
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
find . -name '*.bak' -delete
find . -name "#*#" -print -delete

rm -f geth_server.out
rm -f .node-xmlhttprequest*
rm -f ipfs.out
rm -f modified_date.txt
rm -f package-lock.json
# rm -f .oc.pckl
rm -f base/meta_data.json

rm -rf docs/_build_html/
rm -rf docs/_build/

# pyclean

printf "cleaning [ ${GREEN}SUCCESS${NC} ]\n"
