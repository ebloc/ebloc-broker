import binascii

import base58

Qm = b"\x12 "


def convertBytes32Ipfs(bytes_array):
    bytes_init = base58.b58decode("Qm")
    merge = Qm + bytes_array
    return base58.b58encode(merge).decode("utf-8")


def convertIpfsBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def IPFS_chech(greeter, chain, web3):
    ipfsHash = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vz"
    hex_str = convertIpfsBytes32(ipfsHash)  # "7d5a99f603f231d53a4f39d1521f98d2e8bb279cf29bebfd0687dc98458e7f89";
    data = web3.toBytes(hexstr=hex_str)
    set_txn_hash = greeter.transact().setGreeting(data)
    contract_address = chain.wait.for_receipt(set_txn_hash)
    print("setGreeting_" + "gasUsed=" + str(contract_address["gasUsed"]))

    ret = greeter.call().greet()
    ret = ret.encode("latin-1")
    ipfsHashRet = convertBytes32Ipfs(ret)
    assert ipfsHash == ipfsHashRet


def combineUint128(variable1, variable2):
    bits1 = "{0:0128b}".format(variable1)
    bits2 = "{0:0128b}".format(variable2)
    # print(bits1 + bits2)
    return int(bits1 + bits2, 2)


def test_custom_greeting(web3, chain):
    print("\n")
    greeter, _ = chain.provider.get_or_deploy_contract("Greeter")
    IPFS_chech(greeter, chain, web3)

    key = "acfd2fd8a1e9ccf031db0a93a861f6eb"
    set_txn_hash = greeter.transact().mapWorkflow(key)
    contract_address = chain.wait.for_receipt(set_txn_hash)
    print("mapWorkflow_" + "gasUsed=" + str(contract_address["gasUsed"]))

    # ===
    v1 = 340282366920938463463374607431768211455
    resInt = combineUint128(v1, v1)
    print(resInt)
    set_txn_hash = greeter.transact().setCharacter(resInt)

    print(greeter.call().getVariables())

    print(greeter.call().getDoo())

    # ===
    array = [
        0,
        1,
        2,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
    ]
    array = [0]
    set_txn_hash = greeter.transact().array(array)

    print(greeter.call().getMoo())
