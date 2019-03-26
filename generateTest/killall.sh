#!/bin/bash

sudo kill -9 $(ps aux | grep "[t]est"  | awk '{print $2}')
