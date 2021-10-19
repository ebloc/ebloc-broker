#!/bin/bash
# doc: https://stackoverflow.com/a/58673788/2402577

clean.sh
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*
