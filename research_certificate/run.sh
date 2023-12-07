#!/bin/bash

pytest tests --capture=sys -s -x -k "test_roc" --disable-pytest-warnings -vv --tb=line
