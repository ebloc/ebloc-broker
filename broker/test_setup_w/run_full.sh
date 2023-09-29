#!/bin/bash

# ./run.sh 32 56
# ./run.sh 64 112
# ./run.sh 128 224
# ./run.sh 256 448
# ./run.sh 512 1100  # this one is 2.15x

# ./my_scheduler.py 32 56
# ./my_scheduler.py 64 112
# ./my_scheduler.py 128 224
./my_scheduler.py 256 448 && \
    ./my_scheduler.py 512 1100

./my_layer_heft.py 32 56 && \
    ./my_layer_heft.py 64 112 && \
    ./my_layer_heft.py 128 224 && \
    ./my_layer_heft.py 256 448 && \
    ./my_layer_heft.py 512 1100
