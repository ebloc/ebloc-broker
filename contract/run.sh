#!/bin/bash

py.test --capture=fd tests/test.py -s --disable-pytest-warnings
