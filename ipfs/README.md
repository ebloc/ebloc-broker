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

```
go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen
ipfs-swarm-key-gen > ~/.ipfs/swarm.key
```
