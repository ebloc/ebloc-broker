#!/bin/bash

wget -O geth.md https://raw.githubusercontent.com/ebloc/eBlocPOA/master/README.md
mv geth.md source/geth.md
cp $HOME/ebloc-broker/README.md ~/ebloc-broker/docs/convert/source/readme.md
./convert_md_2_rst.py

mv source/readme.rst ../quickstart.rst
mv source/geth.rst   ../connect.rst
