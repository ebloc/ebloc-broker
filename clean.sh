#!/bin/bash                  
#                            |
# To Run:  sudo bash clean.sh|
#-----------------------------

pyclean docs/

find . -name '*.pyc' -delete
find . -name 'nohup.out' -delete
find . -name '*.*~' -delete

rm -f  contractCalls/*.*~
rm -f checkSinfoOut.txt
rm -f .node-xmlhttprequest*

rm -f docs/*.*~
rm -f ./docs/solidity_lexer.pyc
rm -f ipfs.out
rm -f modifiedDate.txt
rm -f \#*
rm -f package-lock.json

rm -rf contract/tests/__pycache__/
rm -rf contractCalls/__pycache__/
rm -rf docs/_build_html/
rm -rf docs/__pycache__/
rm -rf __pycache__/
rm -rf docs/_build/
