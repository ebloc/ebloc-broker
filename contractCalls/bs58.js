exports.bs58_decode = function(var1) {
    const bs58 = require('bs58')
    return bs58.decode(var1).toString('hex')
};

exports.bs58_encode = function(var1) {
    const bs58 = require('bs58')
    bytes = Buffer.from(var1, 'hex')
    return bs58.encode(bytes)
};

if(process.argv[2] == "encode"){
    str=exports.bs58_decode(process.argv[3]);
    console.log("0x" + str.substr(4));
}

if(process.argv[2] == "decode"){
    str=exports.bs58_encode(process.argv[3]);
    console.log("0x" + str)
}
