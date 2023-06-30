#!/bin/bash

CURRENT_DIR=$(PWD)
DIR=~/ebloc-broker/
org-ruby --translate markdown $DIR/README.org > $DIR/.docs/convert/source/readme.md
org-ruby --translate markdown $DIR/.docs/accounts.org > $DIR/.docs/convert/source/accounts.md
org-ruby --translate markdown $DIR/.docs/gdrive.org > $DIR/.docs/convert/source/gdrive_readme.md
org-ruby --translate markdown $DIR/.docs/quickstart.org > $DIR/.docs/convert/source/quickstart.md

# cp /Users/alper/Documents/research/TSC_eBlocPOA/lkmpg/main.md $DIR/docs/convert/source/cost_example.md

gsed -i "1s/.*/# ebloc-broker/" $DIR/.docs/convert/source/readme.md

# finally
cd $DIR/.docs/convert/
~/venv/bin/python3 convert_md_to_rst.py

gsed -i "s/file:\/docs\//\.\.\ image\:\:\ /" source/readme.rst

rsync --checksum source/readme.rst $DIR/docs/index.rst
rsync --checksum source/accounts.rst $DIR/docs/
rsync --checksum source/gdrive_readme.rst $DIR/docs/
rsync --checksum source/quickstart.rst $DIR/docs/

# cp source/cost_example.rst $DIR/docs/

echo "[ok]"

# file:/docs/

# wget -O geth.md https://raw.githubusercontent.com/ebloc/eBlocPOA/master/README.md
# mv geth.md source/geth.md
# cp $HOME/ebloc-broker/README.md ~/ebloc-broker/docs/convert/source/readme.md

# mv source/readme.rst ../quickstart.rst
# mv source/geth.rst   ../connect.rst
