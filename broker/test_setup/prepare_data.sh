#!/bin/bash

rename_all () {
    # medium
    mv -v babyface.n26c10 fe801973c5b22ef6861f2ea79dc1eb9c
    mv -v BL06-camel-lrg 0d6c3288ef71d89fb93734972d4eb903
    mv -v BL06-gargoyle-lrg 4613abc322e8f2fdeae9a5dd10f17540
    mv -v adhead.n6c100 050e6cc8dd7e889bf7874689f1e1ead6
    mv -v adhead.n6c10 9d5d892a63b5758090258300a59eb389
    mv -v babyface.n26c100 779745f315060d1bc0cd44b7266fb4da
    mv -v bone.n6c100 dd0fbccccf7a198681ab838c67b68fbf
    mv -v bone.n6c10 45281dfec4618e5d20570812dea38760
    mv -v bone.n26c10 bfc83d9f6d5c3d68ca09499190851e86
    mv -v liver.n26c100 8f6faf6cfd245cae1b5feb11ae9eb3cf
    mv -v liver.n26c10 1bfca57fe54bc46ba948023f754521d6
    mv -v BL06-gargoyle-med f71df9d36cd519d80a3302114779741d
    #
    mv -v babyface.n6c100 f1de03edab51f281815c3c1e5ecb88c6
    mv -v babyface.n6c10 082d2a71d86a64250f06be14c55ca27e
    mv -v BL06-camel-med 03919732a417cb1d14049844b9de0f47
    mv -v BL06-camel-sml 983b9fe8a85b543dd5a4a75d031f1091
    mv -v BL06-gargoyle-sml b6aaf03752dc68d625fc57b451faa2bf
    mv -v BVZ-sawtooth c0fee5472f3c956ba759fd54f1fe843e
    mv -v BVZ-tsukuba 63ffd1da6122e3fe9f63b1e7fcac1ff5
    mv -v BVZ-venus 9e8918ff9903e3314451bf2943296d31
    mv -v KZ2-sawtooth eaf488aea87a13a0bea5b83a41f3d49a
    mv -v KZ2-tsukuba e62593609805db0cd3a028194afb43b1
    mv -v KZ2-venus 3b0f75445e662dc87e28d60a5b13cd43
    mv -v LB07-bunny-med ebe53bd498a9f6446cd77d9252a9847c
    mv -v LB07-bunny-sml f82aa511f8631bfc9a82fe6fa30f4b52
    mv -v liver.n6c100 761691119cedfb9836a78a08742b14cc
    mv -v liver.n6c10 f93b9a9f63447e0e086322b8416d4a39
}

extract () {
    tar -xvf ~/.share/small.tar.gz -C /var/ebloc-broker/cache
    tar -xvf ~/.share/medium.tar.gz -C /var/ebloc-broker/cache
    cd /var/ebloc-broker/cache
    mv small/* .
    mv medium/* .
    rmdir ./*
    rename_all
}


main() {
    :
    # extract
}

main "$@"
