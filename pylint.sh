#!/bin/bash

find . -type f -name "*.py" | xargs pylint -E | grep E0611
