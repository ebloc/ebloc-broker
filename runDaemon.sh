#!/bin/bash

nohup python -u Driver.py &
sudo tail -f  nohup.out
