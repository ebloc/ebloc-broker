#!/bin/bash

source $HOME/venv/bin/activate
rm -rf build/
brownie compile --all
