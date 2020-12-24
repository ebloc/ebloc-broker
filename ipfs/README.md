# Enable Google-Instance:

- VPN network => Firewall => Create Firewall rule

```
default-ipfs
Ingress
http-server
IP ranges: 0.0.0.0/0
tcp:4001
Allow
1000
default
Off
```

- Open instance, edit, network tags => add `default-ipfs`

----------------

# Private Networks

- Link: https://github.com/ipfs/go-ipfs/blob/master/docs/experimental-features.md#private-networks
- For the main node:

```
go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen
ipfs-swarm-key-gen > ~/.ipfs/swarm.key


```

# All nodes:

```
export LIBP2P_FORCE_PNET=1 && IPFS_PATH=~/.ipfs ipfs daemon
```

```
ipfs bootstrap rm --all
ipfs bootstrap add /ip4/34.89.13.197/tcp/4001/p2p/12D3KooWHpiUYZ8ET4Qb8uywNKBMFioYmV1MpTwKktz8LS4FXfer

echo "/key/swarm/psk/1.0.0/
/base16/
d0e4cbcfad1f5a945bf8e44ddf8de5da87a7d5418072470419f7cbb2f83fd607" > ~/.ipfs/swarm.key
```

# For home and home2

```
ipfs swarm connect
/ip4/192.168.1.3/tcp/4001/p2p/12D3KooWSE6pY7t5NxMLiGd4h7oba6XqxJFD2KNZTQFEjWLeHKsd
```
