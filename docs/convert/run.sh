#!/bin/bash

cp ../../README.md source/readme.md
python convert_md_2_rst.py
cp source/readme.rst           ../quickstart.rst
cp source/issue1.rst           ../connect.rst
tail -n+3 source/issue7.rst >> ../connect.rst

