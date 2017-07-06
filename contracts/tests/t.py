#!/usr/bin/pythonA
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

    print( "\nReceipt Used Gas: " + str(contract_address["gasUsed"]) + "\n" )
    return;


def receiptCheck(my_contract, chain, s, e, ipfsHash, index,):
    #set_txn_hash     = my_contract.transact().receiptCheck( s, e, ipfsHash, index, 60 );#job's run time.
    #hex_string = "7D5A99F603F231D53A4F39D1521F98D2E8BB279CF29BEBFD0687DC98458E7F89";
    #hex_data = hex_string.decode("hex"); #
    #print('dfdsfdsfdsfds '+ hex_data.encode("hex"))

    set_txn_hash     = my_contract.transact().receiptCheck( ipfsHash,index, 60, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve", 0, 100 );#job's run time.


    #set_txn_hash     = my_contract.transact().receiptCheck( ipfsHash, index, 60, ipfsHash, '0' );#job's run time.
    #set_txn_hash     = my_contract.transact().r( s, e, core );
    contract_address = chain.wait.for_receipt(set_txn_hash)
    pushBlockInfo(contract_address);

def test_receipt(web3, accounts, chain):
    global blkArrayIndex;
    global runTime;
    my_contract, _   = chain.provider.get_or_deploy_contract('eBlocBroker');

    print(accounts)

    account = accounts[0];
    print( "\n");
    print( web3.eth.getBalance(accounts[0]) );
    print( web3.eth.getBalance(accounts[1]) );
    print( web3.eth.getBalance(accounts[2]) );
    print( web3.eth.getBalance(accounts[3]) );
    print( web3.eth.getBalance(accounts[4]) );
    print( web3.eth.getBalance(accounts[5]) );
    print( web3.eth.getBalance(accounts[6]) );
    print( web3.eth.getBalance(accounts[7]) );
    print( web3.eth.getBalance(accounts[8]) );

    print(account);
    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().registerCluster( 128, "alperalperalper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1000000000000000, "0x");
    contract_address = chain.wait.for_receipt(set_txn_hash)

    set_txn_hash     = my_contract.transact().updateCluster( 128, "alper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1000000000000000, "0x");   

    #name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsId = my_contract.call().getClusterInfo(account);
    #print("ClusterName: " + federationCloudId)


    #Assign core Hour Part. start!!!
    #output_1 = my_contract.call().getCoreBalance( account, account     );
    #output_2 = my_contract.call().getCoreBalance( account, accounts[1] );
    #print( str(output_1) + " " + str(output_2) );

    #set_txn_hash     = my_contract.transact().assignCoreHours(account, "0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e", 100 );
    #contract_address = chain.wait.for_receipt(set_txn_hash)

    #output_1 = my_contract.call().getCoreBalance( account, account     );
    #output_2 = my_contract.call().getCoreBalance( account, accounts[1] );
    #print( str(output_1) + " " + str(output_2) );

    #Assign core Hour Part. ended!!!


    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().deregisterCluster( );
    contract_address = chain.wait.for_receipt(set_txn_hash)

    web3.eth.defaultAccount = accounts[0];
    set_txn_hash     = my_contract.transact().registerCluster( 128, "alperalperalper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 1000000000000000, "0x");

    #set_txn_hash     = my_contract.transact().n();
    #contract_address = chain.wait.for_receipt(set_txn_hash)


    #set_txn_hash     = my_contract.transact().NumTest();
    #contract_address = chain.wait.for_receipt(set_txn_hash)

    contract_address = chain.wait.for_receipt(set_txn_hash)
    print(contract_address)
    initial_myGas = contract_address["gasUsed"];
    print("usedGas empty:23499: " + str(initial_myGas));
    #print(initial_myGas);
    #web3.coinbase = accounts[0];
    #web3.coinbase
    web3.eth.defaultAccount = accounts[2];
    set_txn_hash     = my_contract.transact().registerCluster(128, "alper", "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu", "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ", 10000000000000000, "0x");
    contract_address = chain.wait.for_receipt(set_txn_hash)
    #account = accounts[1];

    o = my_contract.call().getClusterAddresses();
    print(set_txn_hash);
    print(o);


    #output           = my_contract.call().number();
    #print(output);
    #print("Total score for %d " % (output))


    j = 0;
    fname = "/Users/alper/Desktop/n.txt";
    f1=open('/Users/alper/Desktop/receipt.txt', 'w+')
    account = accounts[2];
    with open(fname) as f:
        for line in f:
            if( j == 0 ):
                break;

            line = line.rstrip('\n');
            arguments = line.split(" ")
            #if( j > 12209 - 300 ): #300

            receiptCheck(my_contract, chain, int(arguments[0]), int(arguments[1]), 0 ); #, int(arguments[2]) );
            runTime.append( int(arguments[1]) - int(arguments[0]) );
            print( j, arguments[0], arguments[1], arguments[2], myGas );
            f1.write( '%s %s %s %d \n' % (arguments[0], arguments[1], arguments[2], myGas ) )
            #print(my_contract.call().hSize());

            #if( j == 10 ):break;
            j = j + 1;

    hex_string = "amoyRm44U3Q5dHpMZUVyQmlYQTZvaVphdG5Ed0oyWXJuTFkzVXluNG1zRDhr";

    print( "Block_Number: " + str(web3.eth.blockNumber) );
    coreNum = 1;
    set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000*coreNum, "wei") }).submitJob(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", coreNum, "Science", 60, 0, "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k" );
    contract_address = chain.wait.for_receipt(set_txn_hash)
    gUsed = contract_address["gasUsed"];
    print( "\nUsed Gas:" + str(gUsed) + "\n" )
    #return;

    coreNum = 1;
    contract_address = chain.wait.for_receipt(set_txn_hash)
    set_txn_hash     = my_contract.transact({"from": accounts[8], "value": web3.toWei(60*10000000000000000*coreNum, "wei") }).submitJob(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve", coreNum, "Science", 60, 2, "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k" );
    contract_address = chain.wait.for_receipt(set_txn_hash)
    initial_myGas = contract_address["gasUsed"];
    print( "Gas Used on Insert: " + str(initial_myGas) + "-------------------")

    web3.eth.defaultAccount = accounts[2];

    size           = my_contract.call().getJobSize(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve");
    print("JobSize " + str(size) + "----------");


    name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsId = my_contract.call().getClusterInfo(account);
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

    #ipfsOut,jobStatus,jobBlkStart, blknum,jobId,coreMinGas,time, core, r1, r2 = my_contract.call().getJobInfo(account, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0);
    #print("JobInfo: " + str(jobBlkStart)+ " "+ str(time) +"\n")

    receiptCheck(my_contract, chain, 17, 18, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0  );
    #receiptCheck(my_contract, chain, 17, 18, "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd", 0 );

    size = my_contract.call().getClusterReceivedAmount(account);
    print( size );

    print( web3.eth.getBalance(account) );
    print( web3.eth.getBalance(accounts[1]) );
    print( web3.eth.getBalance(accounts[2]) );
    print( web3.eth.getBalance(accounts[3]) );
    print( web3.eth.getBalance(accounts[4]) );
    print( web3.eth.getBalance(accounts[5]) );
    print( web3.eth.getBalance(accounts[6]) );
    print( web3.eth.getBalance(accounts[7]) );
    print( web3.eth.getBalance(accounts[8]) );
    '''
