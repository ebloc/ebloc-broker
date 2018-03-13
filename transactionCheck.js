var nodePaths = require('./nodePaths');
var eBlocBroker = require(nodePaths.EBLOCBROKER + '/eBlocBrokerHeader.js');

var lineReader = require('readline').createInterface({
  input: require('fs').createReadStream('t.txt')
});

max = 0;
lineReader.on('line', function (line) {
    var line = line.split(" ");

    //console.log(line[0])
    tx=line[0]
    max += console.log( '' + eBlocBroker.getTransactionGas(line[0]))  
});

console.log("max: " +  max);
