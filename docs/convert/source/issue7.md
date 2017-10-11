# **How to connect Ethereum eBloc private blockchain**

## **Parity**

### **Dependencies:**
#### **Linux**
` $ curl https://sh.rustup.rs -sSf | sh`
Parity also requires gcc, g++, libssl-dev/openssl, libudev-dev and pkg-config packages to be installed.

#### **OSX**

```
$ curl https://sh.rustup.rs -sSf | sh
source .cargo/env
```

### To Install Parity

- Through .deb:

```
curl -O https://d1h4xl4cr1h0mo.cloudfront.net/v1.6.10/x86_64-unknown-linux-gnu/parity_1.6.10_amd64.deb
sudo dpkg -i parity_1.6.10_amd64.deb
```

- **Build from source**.

```
# download Parity code
$ git clone https://github.com/paritytech/parity
$ cd parity

# build in release mode
$ cargo build --release
```

### Network Setup

`[$] mkdir ebloc-parity && cd ebloc-parity`
Create a file called `parity.json` and paste following code:

```
{
  "name": "Ebloc",
  "engine": {
    "Ethash": {
      "params": {
        "gasLimitBoundDivisor": "0x0400",
        "minimumDifficulty": "0x020000",
        "difficultyBoundDivisor": "0x0800",
        "durationLimit": "0x0d",
        "blockReward": "0x4563918244F40000",
        "registrar": "0x81a4b044831c4f12ba601adb9274516939e9b8a2",
        "homesteadTransition": "0x00",
        "eip150Transition": "0x7fffffffffffffff",
        "eip155Transition": "0x7fffffffffffffff",
        "eip160Transition": "0x7fffffffffffffff",
        "eip161abcTransition": "0x7fffffffffffffff",
        "eip161dTransition": "0x7fffffffffffffff"
      }
    }
  },
  "params": {
    "accountStartNonce": "0x00",
    "maximumExtraDataSize": "0x20",
    "minGasLimit": "0x1388",
    "networkID": "0x5B7E",
    "eip98Transition": "0x7fffffffffffffff"
  },
  "genesis": {
    "seal": {
      "ethereum": {
        "nonce": "",
        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000"
      }
    },
    "difficulty": "0x400",
    "author": "0x3333333333333333333333333333333333333333",
    "timestamp": "0x00",
    "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "extraData": "0x00",
    "gasLimit": "0x3B4A1B44"
  },
  "accounts": {
    "0000000000000000000000000000000000000001": { "builtin": { "name": "ecrecover", "pricing": { "linear": { "base": 3000, "word": 0 } } } },
    "0000000000000000000000000000000000000002": { "builtin": { "name": "sha256", "pricing": { "linear": { "base": 60, "word": 12 } } } },
    "0000000000000000000000000000000000000003": { "builtin": { "name": "ripemd160", "pricing": { "linear": { "base": 600, "word": 120 } } } },
    "0000000000000000000000000000000000000004": { "builtin": { "name": "identity", "pricing": { "linear": { "base": 15, "word": 3 } } } },
    "0xda1e61e853bb8d63b1426295f59cb45a34425b63": { "balance": "1000000000000000000000000000000" }
  }
}
```

Create a file called `myPrivateNetwork.txt` and paste following lines:

```bash
enode://7f3bebdd678d5a0ebe2701b2f7858763f5ce03fc531fe989fb7bb41d2e8e1237ae5b092666171a180afba0c47f1aad055e2bf6e1287fcdc756f183902764eba2@79.123.177.145:3000
enode://4d331051d8fb471c87a9351b36ffb72bf445a9337727d229e03c668f99897264bf11e1b897b1561f5889825e2211b06858139fa469fdf73c64d43a567ea72479@193.140.197.95:3000
enode://9fbac6e71e1478506987872b7d3d6de19681527971ae243044daa44221a99ce5944839cd4057133f18b3610f5c59bb2fd7077fafa208d8eb52918faf06782d48@79.123.177.145:3000
```
### To Run Parity

 `Author` is  the owner of the mined block reward. You your own account where you have created.

```bash
parity --warp --geth --chain parity.json --network-id 23422 --reserved-peers myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --rpccorsdomain=* --author "0x75....." #--unlock $COINBASE --password /home/ubuntu/EBloc/password.txt
```

To attach `Geth` console to `Parity`: `geth attach`

Open your favourite browser and type: localhost:8080 . I observe that google-chrome it better to use with it. Its UI is much better than other apps.
<img width="1039" alt="screen shot 2017-03-23 at 17 35 09" src="https://cloud.githubusercontent.com/assets/18537398/24255800/1e6851ae-0fef-11e7-917e-ca81debe064d.png">

Parity's has a default wrap property: warp sync is downloading snapshots of the state first, so you are basically synced within <60 seconds. and after that it slowly catches up missing blocks
https://github.com/paritytech/parity/wiki/Warp-Sync