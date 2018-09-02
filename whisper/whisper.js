Web3 = require("web3");
web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));     

async function connect() { //note async function declaration
    var kId = await web3.shh.newKeyPair(); 

    var value = await web3.shh.getPrivateKey(kId);
    console.log(value)

}

connect();

