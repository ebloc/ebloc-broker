#!/bin/bash

source $HOME/v/bin/activate
brownie compile
pytest tests -s --capture=no
