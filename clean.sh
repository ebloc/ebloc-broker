#!/bin/bash                  |
#                            |
# To Run:  sudo bash clean.sh|
#-----------------------------

pyclean docs/

rm -f *.pyc
rm -f checkSinfoOut.txt
rm -f .node-xmlhttprequest*
rm -f *.*~
rm -f docs/*.*~
rm -f docs/nohup.out
rm -f nohup.out
rm -f ./docs/solidity_lexer.pyc
rm -f contractCalls/*.*~
rm -f ipfs.out
rm -rf docs/_build_html
rm -f modifiedDate.txt
rm -rf docs/__pycache__
rm -rf contract/tests/__pycache__
rm -rf __pycache__/
rm -rf docs/_build
rm -f \#*
