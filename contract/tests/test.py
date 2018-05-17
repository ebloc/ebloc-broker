#!/usr/bin/python

import os
import StringIO
import pytest

cwd = os.getcwd()

blkArrayIndex = 0;
gasUsed       = [];
blockNumber   = [];
runTime       = [];
myGas         = 0;

def pushBlockInfo(contract_address):
    global blkArrayIndex;
    global gasUsed;
    global blockNumber;
    global flag;

    global myGas;
    myGas = contract_address["gasUsed"];
    gasUsed.append( contract_address["gasUsed"] );
    blockNumber.append( contract_address["blockNumber"] );
    blkArrayIndex = blkArrayIndex + 1;

    print( "Receipt Used Gas: " + str(contract_address["gasUsed"]) )
    return;

def receiptCheck(my_contract, chain, e, ipfsHash, index, timeToRun):
    set_txn_hash     = my_contract.transact().receiptCheck( ipfsHash, index, timeToRun, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve", 0, e );
    contract_address = chain.wait.for_receipt(set_txn_hash)
    pushBlockInfo(contract_address);

def test_receipt(web3, accounts, chain): #{
    web3._requestManager = web3.manager
    global blkArrayIndex;
    global runTime;
    my_contract, _   = chain.provider.get_or_deploy_contract('eBlocBroker');

    print(accounts)

    account = accounts[0];
    print("\n");

    for i in range(0, 9):
        print(web3.eth.getBalance(accounts[i]));

    print(account);
    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().registerCluster(1, "alperalperalper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf");
    contract_address = chain.wait.for_receipt(set_txn_hash)
    print("usedGas registerCluster: " + str(contract_address["gasUsed"]));

    web3.eth.defaultAccount = accounts[8];
    set_txn_hash     = my_contract.transact({"from": accounts[8]}).registerUser("email@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf", '0000-0001-7642-0552', 'ebloc');
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    print("usedGas registerUser: " + str(contract_address["gasUsed"]));

    set_txn_hash     = my_contract.transact({"from": accounts[8]}).registerUser("email@gmail.com", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf", '0000-0001-7642-0552', 'ebloc');
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    print("usedGas registerUser: " + str(contract_address["gasUsed"]));

    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().authenticateORCID('0000-0001-7642-0552'); # ORCID should be registered.
    
    
    print("isUserExist: "           + str(my_contract.call().isUserExist(accounts[8])));
    blockReadFrom, b, c  = my_contract.call().getUserInfo(accounts[8]);
    print("User's blockReadFrom:  " + str(blockReadFrom));

    output = my_contract.call().isUserExist(accounts[1]);
    print("isUserExist: " + str(output));

    web3.eth.defaultAccount = accounts[0];
    output = my_contract.call().isClusterExist(accounts[0]);
    print("isExist: "+str(output));

    blockReadFrom, coreLimit, coreMinutePrice = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));

    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().updateCluster(128, "alper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "0x");   

    blockReadFrom, coreLimit, coreMinutePrice = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));


    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().deregisterCluster();
    contract_address = chain.wait.for_receipt(set_txn_hash)
    
    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().authenticateORCID('alper');
        
    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().registerCluster( 128, "alperalperalper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "0x");

    initial_myGas = contract_address["gasUsed"];
    print("usedGas empty:23499: " + str(initial_myGas));
    #print(initial_myGas);
    #web3.coinbase = accounts[0];
    #web3.coinbase
    web3.eth.defaultAccount = accounts[2];
    set_txn_hash     = my_contract.transact().registerCluster(128, "alper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "0x");
    contract_address = chain.wait.for_receipt(set_txn_hash)   
    
    currBlk = web3.eth.blockNumber;
    j = 0;
    #fname = "/Users/alper/Desktop/n.txt";
    fname = cwd + '/test.txt';    
    f1=open(cwd + '/receipt.txt', 'w+')
    account = accounts[2];
    x = "5b0f93fa7d28bc881f16c14b7c59a58ae5af997e3d0949d7ae6949302bd1f4d0";
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")

            cg      = int(arguments[1]) - int(arguments[0]);
            coreNum = int(arguments[2])

            chain.wait.for_block(int(arguments[0]));
            jobKey     = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd";
            miniLockId = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k";
            
            set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000*coreNum, "wei") }).submitJob(
                account, jobKey, coreNum, "Science", cg, 1);
            contract_address = chain.wait.for_receipt(set_txn_hash)

            print("submitJob: " + str(contract_address["gasUsed"]));
            # print(my_contract.call().getJobInfo('0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d', jobKey, 0));
            j = j + 1;

    
    chain.wait.for_block(100);
    print( "Block_Number: " + str(web3.eth.blockNumber) );

    blockReadFrom, coreLimit, coreMinutePrice  = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));

    val = 0;
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")
            set_txn_hash     = my_contract.transact().setJobStatus("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", val, 4, int(arguments[0]) );    
            val = val + 1

    val = 0;
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")
            receiptCheck(my_contract, chain, int(arguments[1]), "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", val, int(arguments[1]));

            size = my_contract.call().getClusterReceivedAmount(account);
            print(size);
            val = val + 1

    # Prints finalize version of the linked list.
    size = my_contract.call().getClusterReceiptSize(account);
    for i in range(0, size):
        print(my_contract.call().getClusterReceiptNode(account, i));

    print("END");
    print(".");
#}
