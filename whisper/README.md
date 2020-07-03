## Whisper

# Sender:

```
message="Hello there!"
web3.shh.post({
  pubKey: '0x04d96278caa49aff29d76399001a43a9a8005da21c6853d20d6af11d61df8a2a25de0fe79a1099bd4b915445d94cbd448b2fe548fb53fed5d887291f35de0f44c9',
  ttl: 600,
  topic: '0x07678231',
  powTarget: 2.01,
  powTime: 3,
  payload: web3.fromAscii(message)
  });
```
