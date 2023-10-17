#!/bin/bash

reset_start_end () {
    # leo
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.117:/home/alper/.ebloc-broker/start.sh
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.117:/home/alper/.ebloc-broker/end.sh

    # leo1
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.21:/home/alper/.ebloc-broker/start.sh
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.21:/home/alper/.ebloc-broker/end.sh

    # leo2
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.104:/home/alper/.ebloc-broker/start.sh
    scp ~/ebloc-broker/broker/test_setup_w/bare.sh alper@192.168.1.104:/home/alper/.ebloc-broker/end.sh
}

# reset_start_end
# ./my_scheduler.py 128 224

# reset_start_end
# ./my_scheduler.py 256 448

reset_start_end
./my_layer_heft.py 128 224

reset_start_end
./my_layer_heft.py 256 448

reset_start_end

# ./run.sh 32 56
# ./run.sh 64 112
# ./run.sh 128 224
# ./run.sh 256 448
# ./run.sh 512 1100  # this one is 2.15x

# ./my_scheduler.py 16 28
# ./my_scheduler.py 32 56 && reset_start_end && \
#     ./my_scheduler.py 64 112 && reset_start_end && \
#     ./my_scheduler.py 128 224 && reset_start_end && \
#     ./my_scheduler.py 256 448
# ./my_scheduler.py 512 1100

# ./my_layer_heft.py 32 56 && \
#     ./my_layer_heft.py 64 112 && \
#     ./my_layer_heft.py 128 224 && \
#     ./my_layer_heft.py 256 448 && \
#     ./my_layer_heft.py 512 1100
