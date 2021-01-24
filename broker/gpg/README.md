# Provider

```
gpg --keyserver hkp://pgp.mit.edu --send-keys <key_id>
```

# Requester

See https://stackoverflow.com/a/34132924/2402577 for more info.

```
keyid="11FBA2D03D3CFED18FC71D033B127BC747AADC1C"
gpg --keyserver pgp.mit.edu --search-keys $keyid
gpg --edit-key $keyid
> trust
> quit
```
