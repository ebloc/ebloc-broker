#!/bin/bash

sudo kill -9 $(ps aux | grep -E "python.*[t]est"  | awk '{print $2}')
