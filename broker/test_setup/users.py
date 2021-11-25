#!/usr/bin/env python3

from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log

collect_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()

providers = [
    "0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA",
    "0x765508fc8f78a465f518ae79897d0e4b249e82dc",
    "0x38cc03c7e2a7d2acce50045141633ecdcf477e9a",
    "0xeab50158e8e51de21616307a99c9604c1c453a02",
]

users = [
    "0x378181ce7b07e8dd749c6f42772574441b20e35f",
    "0x4cd57387cc4414be8cece4e6ab84a7dd641eab25",
    "0x02a07535bc88f180ecf9f7c6fd66c0c8941fd7ab",
    "0x90b25485fcbde99f3ca4864792947cfcfb071de6",
    "0x449ecd91143d77cfa9fbd4a5ba779a0911d21423",
    "0x1397e8bf32d57b46f507ff2e912a29cd9aa78dcd",
    "0xdce54cfd06e7ccf5f2e7640e0007ba667190e38e",
    "0x5affc0638b7b311be40a0e27ed5cd7c133c16e64",
    "0xd118b6ef83ccf11b34331f1e7285542ddf70bc49",
    "0x904c343addd9f21510e711564dbf52d2a0daf7e3",
    "0x17b4ec0bcd6a8f386b354becd44b3c4813448184",
    "0x6e89235ddcc313a8184ffa4cea496d0f42f1f647",
    "0x76f47f566845d7499c058c3a36ccd2fe5695c9f7",
    "0xb0c24da05236caae4b2ee964052aa917eb3927ed",
    "0x1176e979939e9a0ea65b9ece552fe413747243dc",
    "0x24056c57e3b0933d2fa7d83fb9667d0efdfae64d",
    "0x5c2719b9f74dba2feaefb872ffaf6a375c8e70f9",
    "0x30f02cecf3e824f963cfa05270c8993a49703d55",
    "0x44d85663b00117e38a9d6def322fb09dc40b6839",
    "0x78bc08e70dce53f7823456e34610bc55828373af",
    "0x4934a70ba8c1c3acfa72e809118bdd9048563a24",
    "0x7293d2089b6f6e814240d21dc869cc88a3471839",
    "0x141c01e36d4e908d42437e203442cd3af40b4d79",
    "0x782cf10b0c7393c0c98587277bfc26e73d3d0ca2",
    "0x51e2b36469cdbf58863db70cc38652da84d20c67",
    "0x66b7bf743b17f05f8a5afff687f085dc88ed3515",
    "0xbe2a4e39b6853086aab31d4003e2d1fa67561eae",
    "0xbc28a0dab6eaef04574e2116059bb9102aa31e42",
    "0x8d9fc9ad8d51647a12b52d74cfab6f5948687084",
    "0x67613da8568ae0b0e76796ec8c45b50c469e3f30",
    "0x71cef32e92caacee9bb3b020e2c1b2007d360c26",
    "0x90018b8b5ccf4c291b64d85fdd3d9e179706da26",
    "0xd3ff698232ac001ce663992b316510a50e93e460",
    "0x4c2aebf67f8cfce387ad0ee3774bb193c4a62ef6",
    "0x6d00e4661e8407f24b2942149ea4a9d445d10038",
    "0x92086404471d0e5453f856363358967308b37cd5",
    "0xf6261f330f75052c84022bf3c165153c36d0fcdc",
    "0xd1e34cbda0d77407bbe76cce19d2e11257d00a1b",
    "0x00ddbcfcee1e3222fa8abc2b2b9d319b61993e27",
    "0x6f8d2420c6917bb5bb84db7bc615b9893aa30cb3",
    "0xa0cadcbabd102b7966b82f3556c436e5d88daf07",
    "0xada6c7bc6c6e0004b407733e3993f65397b321ab",
    "0x740fcbc6d4e7e5102b8cba29370b93c6de4c786e",
    "0x2cc6d89cda9db6592f36d548d5ced9ec27a80d5c",
    "0x82b506dee5091b58a85b52bc31681f29d2c55584",
    "0x12ba09353d5c8af8cb362d6ff1d782c1e195b571",
    "0x53cf1a8d668ef8e0de626ceed58e1766c08bb625",
    "0xcf1c9e9f33d3e439e51d065e0ebfccad6850cbd9",
    "0x945ec7ca40720991f4a387e1b19217fbff62cbde",
    "0xa61bb920ef738eab3d296c0c983a660f6492e1af",
    "0xf4c8345baab83d92a88420b093a96dcdb08705de",
    "0xd00440d20faba4a08b3f80f1596420ae16a9910b",
    "0xe01eda38f7b5146463872f0c769ac14885dbf518",
    "0x5ae3a2b79537f849eabb235401645982a2b1d7bd",
    "0xc660aba0006e51cd79428f179467a8d7fbcf90f7",
    "0x64b570f0e7c019dc750c4a75c33dca55bdc51845",
    "0xf6d9f88fa98d4dc427ffdb1bdf01860fd12c98c7",
    "0x29e613b04125c16db3f3613563bfdd0ba24cb629",
    "0x865fdb0532b1579ee4eebf0096dbde06f1548a36",
    "0x676b8d6e031a394c079fc8fee03ad2974ef126f5",
    "0x77c0b42b5c358ff7c97e268794b9ff6a278a0f1e",
    "0x6579dac76f0a009f996270bd1b7716ed72cdb2ce",
    "0x7621e307269e5d9d4d27fd1c24425b210048f486",
    "0xe72307313f8b8f96cfcd99ecef0f1ab03d28be5d",
    "0xfe0f02d3d387eec745090c756a31a3c3c2bf32cf",
    "0x831854a093f30acb032ab9eeaeb715b37ee1bb03",
    "0x1926b36af775e1312fdebcc46303ecae50d945af",
    "0x28fe7b65c3846541d6d17271585792805ae280f7",
    "0xfce73328daf1ae024d0a724c595e1d5b2ac8aecb",
    "0x805332ee379269b087c8c1b96adb0f398d53e46f",
    "0xe953a99ff799e6da23948ca876fce3f264447de8",
    "0x55414e26855c90056b3b54f797b5c7e6558146b3",
    "0x1099f0f45f5f2040cc408b062557a31bfedd00d6",
    "0x7553a853a45358103ac9650d50d4a15ade1038e3",
    "0x5170a965650fc8704b748548c97edb80fec5efd3",
    "0xc23aae5daa9e66d6db8496ada096b447297cbddd",
    "0xc60409093861fe191ae851572a440deb42818a63",
    "0xa47a5e1206e3b8c5fca11f5064d4c0d35e2fd240",
    "0xf767b0567a2c4c6c4b4d071746b68198dddb7202",
    "0x382f1e1fe7680315053ea1c489b4fc003ff9ad64",
    "0x3d50f068445c457c0c38d52980a5e6442e780d89",
    "0x8b7356a95c8ba1846eb963fd127741730f666ba8",
    "0x4d96ba91f490eca2abd5a93f084ad779c54656aa",
    "0x1b8a68bc837f5325bdc57804c26922d98a0332ab",
    "0x4b419991c9b949b20556ab9ad13c5d54354f601f",
    "0x13fe0b65bdd902d252d0b431aec6acf02a0b2f41",
    "0x96963310153ec9a47a19312719a98cc08041134d",
    "0x2c73a80956516ba9e6005030faed2f8212bc10a3",
    "0xb9a498c3a76049bffc96c898605758620f459244",
    "0xf8b8cac4f133b039d1990e9d578289c32ff774de",
    "0xfb674750e02afa2f47f26a2d59ea1fe20444b250",
    "0x6b781119b8ff1c7585f97caf779be6a80a88daf0",
    "0xcaa482f269dd0926fdfd5c48e3a22b621f9d1a09",
    "0x446aa04436809c130eab8e33ce9f5d3c80564fb7",
    "0xd1806d39a8c2cd7469048f6d99c26cb66cd46f83",
    "0xee516025bf14f7118aa9ced5eb2adacfd5827d14",
    "0x1d16cfb236f5830875716c86f600dd2ee7456515",
    "0xe2969f599cb904e9a808ec7218bc14fcfa346965",
    "0x0636278cbd420368b1238ab204b1073df9cc1c5c",
    "0x72c1a89ff3606aa29686ba8d29e28dccff06430a",
]

extra_users = [
    "0x168cb3240a429c899a74aacda4289f4658ec924b",
    "0x08b003717bfab7a80b17b51c32223460fe9efe2a",
    "0x4aae9220409e1c4d74ac95ba14edb0684a431379",
    "0xab608a70d0b4a3a288dd68a1661cdb8b6c742672",
    "0xe2e146d6b456760150d78819af7d276a1223a6d4",
    "0xa9fc23943e48a3efd35bbdd440932f123d05b697",
    "0x5b235d87f3fab61f87d238c11f6790dec1cde736",
    "0xe03914783115e807d8ea1660dbdcb4f5b2f969c0",
    "0x85fa5e6dd9843cce8f67f4797a96a156c3c79c25",
]

Ebb = cfg.Ebb
_collect_account = collect_account.replace("0x", "")
fname = Path(expanduser("~/.brownie/accounts")) / _collect_account
_collect_account = Ebb.brownie_load_account(str(fname), "alper")
log(f"collect_account={Ebb._get_balance(collect_account)}", "bold")
breakpoint()  # DEBUG


def collect_all_into_base():
    for account in extra_users:
        _account = account.lower().replace("0x", "")
        fname = Path(expanduser("~/.brownie/accounts")) / _account
        print(fname)
        account = Ebb.brownie_load_account(str(fname), "alper")
        balance_to_transfer = Ebb._get_balance(account, "wei")
        log(balance_to_transfer)
        log(Ebb._get_balance(collect_account, "wei"))
        if balance_to_transfer > 21000:
            tx = Ebb.transfer(balance_to_transfer - 21000, account, collect_account, required_confs=0)
            log(tx)
            log(Ebb._get_balance(account))
            log(Ebb._get_balance(collect_account))


def send_eth_to_users(accounts, value):
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fname = Path(expanduser("~/.brownie/accounts")) / _account
        print(fname)
        account = Ebb.brownie_load_account(str(fname), "alper")
        log(Ebb._get_balance(collect_account, "wei"))
        tx = Ebb.transfer(value, _collect_account, account, required_confs=0)
        log(tx)
        log(Ebb._get_balance(account))
        log(Ebb._get_balance(collect_account))
        # breakpoint()  # DEBUG


def main():
    collect_all_into_base()
    # send_eth_to_users(providers, "0.5 ether")
    # send_eth_to_users(users, "0.2 ether")


if __name__ == "__main__":
    main()
