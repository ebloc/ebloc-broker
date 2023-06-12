# Create an account to use bloxberg

Use following command to generate an address.
```bash
geth account new
```

Link: [https://geth.ethereum.org/docs/fundamentals/account-management](https://geth.ethereum.org/docs/fundamentals/account-management)

Example output:

```bash
INFO Your new key was generated             address=0x7d1477746A28f6571A9f80aDcd80cDb85e19fc75
WARN [06-08|18:36:15.176] Please backup your key file!
path=/home/user/.ethereum/keystore/UTC--2023-06-08T18-36-11.289938189Z--7d1477746a28f6571a9f80adcd80cdb85e19fc75
WARN [06-08|18:36:15.176] Please remember your password!
Generated account 0x7d1477746A28f6571A9f80aDcd80cDb85e19fc75
```

Afterwards, copy your keystore file into the docker's shared folder.

```bash
fn="~/.ethereum/keystore/UTC--2023-06-08T18-36-11.289938189Z--7d1477746a28f6571a9f80adcd80cdb85e19fc75"
cp $fn ~/ebloc-broker/docker/config/$fn.json
```

Inside the docker instance you should see you keystore file under the folder called `/root/.brownie/accounts/`.

```bash
root@home:~/.brownie/accounts$ tree .
.
└── UTC--2023-06-08T21-10-42.906787000Z--9cd7979681f34622165ec9b498397f56660da74c.json
```

Finally, request `berg` from [https://faucet.bloxberg.org](https://faucet.bloxberg.org) for the generated account address.
