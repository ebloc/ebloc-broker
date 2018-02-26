#!/usr/bin/python
import StringIO
import pytest

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
    set_txn_hash     = my_contract.transact().receiptCheck( ipfsHash, index, timeToRun, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve", 0, e );#job's run time.
    contract_address = chain.wait.for_receipt(set_txn_hash)
    pushBlockInfo(contract_address);

def test_receipt(web3, accounts, chain):
    web3._requestManager = web3.manager
    global blkArrayIndex;
    global runTime;
    my_contract, _   = chain.provider.get_or_deploy_contract('eBlocBroker');

    print(accounts)

    account = accounts[0];
    print( "\n");
    '''
    print( web3.eth.getBalance(accounts[0]) );
    print( web3.eth.getBalance(accounts[1]) );
    print( web3.eth.getBalance(accounts[2]) );
    print( web3.eth.getBalance(accounts[3]) );
    print( web3.eth.getBalance(accounts[4]) );
    print( web3.eth.getBalance(accounts[5]) );
    print( web3.eth.getBalance(accounts[6]) );
    print( web3.eth.getBalance(accounts[7]) );
    print( web3.eth.getBalance(accounts[8]) );
    '''
    print(account);
    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().registerCluster( 1, "alperalperalper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "0x");
    contract_address = chain.wait.for_receipt(set_txn_hash)

    output = my_contract.call().isClusterExist(accounts[0]);
    print("isExist:");
    print(output);
       
    name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsId = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));

    set_txn_hash     = my_contract.transact().updateCluster( 128, "alper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1, "0x");   

    name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsId = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));


    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().deregisterCluster( );
    contract_address = chain.wait.for_receipt(set_txn_hash)

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
    fname = "/Users/alper/ebloc_eblocBrokerGit/contracts/test.txt";    
    f1=open('/Users/alper/Desktop/receipt.txt', 'w+')
    account = accounts[2];
    x = "5b0f93fa7d28bc881f16c14b7c59a58ae5af997e3d0949d7ae6949302bd1f4d0";
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip('\n').split(" ")

            cg      = int(arguments[1]) - int(arguments[0]);
            coreNum = int(arguments[2])

            chain.wait.for_block(int(arguments[0]));

            #jobKey_Description_miniLockId
            set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000*coreNum, "wei") }).submitJob(
                account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", coreNum, "Science", cg, 0, "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k" );

            contract_address = chain.wait.for_receipt(set_txn_hash)

            gas = contract_address["gasUsed"];
            print("submitJobb: " + str(gas));

            #print( j, arguments[0], arguments[1], arguments[2], gas );
            #f1.write( '%s %s %s %d \n' % (arguments[0], arguments[1], arguments[2], myGas ) )
            #print(my_contract.call().hSize());
            j = j + 1;

    
    chain.wait.for_block(100);
    print( "Block_Number: " + str(web3.eth.blockNumber) );

    '''
    coreNum = 1;
    contract_address = chain.wait.for_receipt(set_txn_hash)
    gUsed = contract_address["gasUsed"];
    print( "\nsubmitJobUsedGas:" + str(gUsed) + "\n" )

    coreNum = 127;
    contract_address = chain.wait.for_receipt(set_txn_hash)
    set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000*coreNum, "wei") }).submitJob(
        account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", coreNum, "Science", 60, 0, "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k" );
    contract_address = chain.wait.for_receipt(set_txn_hash)
    initial_myGas = contract_address["gasUsed"];
    print( "Gas Used on Insert: " + str(initial_myGas) + "-------------------")

    
    web3.eth.defaultAccount = accounts[2];

    size           = my_contract.call().getJobSize(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve");
    print("JobSize " + str(size) + "----------");
    '''
    name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsId = my_contract.call().getClusterInfo(account);
    print("Cluster's coreLimit:  " + str(coreLimit));

    val = 0;
    with open(fname) as f:
        for line in f:
            #print(line)
            arguments = line.rstrip('\n').split(" ")
            set_txn_hash     = my_contract.transact().setJobStatus("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", val, 3, int(arguments[0]) );    
            val = val + 1

    val = 0;
    with open(fname) as f:
        for line in f:
            #if(val ==2):
            #break;
            arguments = line.rstrip('\n').split(" ")
            receiptCheck(my_contract, chain, int(arguments[1]), "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", val, int(arguments[1]) - int(arguments[0]) );

            size = my_contract.call().getClusterReceivedAmount(account);
            print( size );

            #print( web3.eth.getBalance(accounts[8]) );
            val = val + 1

            
    size = my_contract.call().getClusterReceiptSize(account);
    for i in range(0, size):
        print(my_contract.call().getClusterReceiptNode(account, i));



    '''
    print("Cluster's federationCloudId:  " + str(federationCloudId));
    print("Cluster's miniLockId:  "        + str(miniLockId));

    #set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000, "wei") }).submitJob(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve", 128, "Science", 0 , 0, 60 );
    #contract_address = chain.wait.for_receipt(set_txn_hash)

    web3.eth.defaultAccount = accounts[2];
    print( "Block_Number: " + str(web3.eth.blockNumber) );

    web3.eth.defaultAccount = accounts[2];
    set_txn_hash     = my_contract.transact().setJobStatus("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0, 3, 10);
    set_txn_hash     = my_contract.transact().setJobStatus("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0, 3, 10);



    #receiptCheck(my_contract, chain, 17, 18, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0 );


    print( web3.eth.getBalance(account) );
    print( web3.eth.getBalance(accounts[1]) );
    '''
    print("END") ;


#set_txn_hash     = my_contract.transact().receiptCheck( s, e, ipfsHash, index, 60 );#job's run time.
#hex_string = "7D5A99F603F231D53A4F39D1521F98D2E8BB279CF29BEBFD0687DC98458E7F89";
#hex_data = hex_string.decode("hex"); #
#print('dfdsfdsfdsfds '+ hex_data.encode("hex"))
#set_txn_hash     = my_contract.transact().receiptCheck( ipfsHash, index, 60, ipfsHash, '0' );#job's run time.
#set_txn_hash     = my_contract.transact().r( s, e, core );
