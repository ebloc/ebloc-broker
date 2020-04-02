#!/bin/bash

git fetch
git checkout origin/master -- README.md

wget -O geth.md https://raw.githubusercontent.com/ebloc/eBlocPOA/master/README.md
mv geth.md source/geth.md
cp ../../README.md source/readme.md

python convert_md_2_rst.py

mv source/readme.rst ../quickstart.rst
mv source/geth.rst   ../connect.rst
