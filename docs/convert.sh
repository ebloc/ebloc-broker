#!/bin/bash

CURRENT_DIR=$(PWD)
DIR=~/ebloc-broker/
org-ruby --translate markdown $DIR/README.org > $DIR/docs/convert/source/readme.md
org-ruby --translate markdown $DIR/docs/accounts.org > $DIR/docs/convert/source/accounts.md
org-ruby --translate markdown $DIR/broker/gdrive/README.org > $DIR/docs/convert/source/gdrive_readme.md
# cp /Users/alper/Documents/research/TSC_eBlocPOA/lkmpg/main.md $DIR/docs/convert/source/cost_example.md

# finally
cd $DIR/docs/convert/
python3 -tt convert_md_2_rst.py

cp source/readme.rst ../index.rst
cp source/accounts.rst ../
cp source/gdrive_readme.rst ../
cp source/cost_example.rst ../

gsed -i "s/file:\/docs\//\.\.\ image\:\:\ /" $DIR/docs/index.rst
echo "[ok]"

# file:/docs/

# wget -O geth.md https://raw.githubusercontent.com/ebloc/eBlocPOA/master/README.md
# mv geth.md source/geth.md
# cp $HOME/ebloc-broker/README.md ~/ebloc-broker/docs/convert/source/readme.md


# mv source/readme.rst ../quickstart.rst
# mv source/geth.rst   ../connect.rst
