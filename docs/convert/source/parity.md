# **How to connect into Private Ethereum Blockchain (eBloc)**

Please note that you can not mine with CPU node using `Parity`. In order to mine you should you `geth` node.

## **Parity**

### **Dependencies:**
#### **Linux:**
` $ curl https://sh.rustup.rs -sSf | sh` . Parity also requires `gcc, g++, libssl-dev/openssl, libudev-dev` and `pkg-config` packages to be installed.

#### **OSX:**

```
$ curl https://sh.rustup.rs -sSf | sh
source .cargo/env
```

### How to Install Parity

- **Through .deb (Try this first)**

```
curl -O https://d1h4xl4cr1h0mo.cloudfront.net/v1.6.10/x86_64-unknown-linux-gnu/parity_1.6.10_amd64.deb
sudo dpkg -i parity_1.6.10_amd64.deb
```

- **Build from source (Try this if .deb installation does not work)**

```
# download Parity code
$ git clone https://github.com/paritytech/parity
$ cd parity

# build in release mode
$ cargo build --release
```
- **Update Parity to the latest version**

```
sudo bash <(curl https://get.parity.io -Lk)
````

------------

### Network Setup

```
git clone https://github.com/ebloc/MyEthereumEbloc_parity.git
cd MyEthereumEbloc_parity
```

#### To Create a New Account

```
parity --geth --force-ui --chain parity.json --network-id 23422 --reserved-peers myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --jsonrpc-cors all account new

Please note that password is NOT RECOVERABLE.
Type password:
Repeat password:
e427c111f968fe4ff6593a37454fdd9abf07c490  //your address is generated 
```

- Inside `.profile` change `COINBASE` variable with the generated account address. For example, you could put your newly created address such as `"0xe427c111f968fe4ff6593a37454fdd9abf07c490"` into `COINBASE`. Do not forget to put `0x` at the beginning of the account.

 `author ` is  the owner of the mined block reward. 

#### To Run

```bash
parity --geth --force-ui --chain parity.json --network-id 23422 --reserved-peers myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --jsonrpc-cors all --author "0x75..." --unlock $COINBASE --password /home/ubuntu/EBloc/password.txt
```

To attach `geth` console to `Parity` do: `geth attach`