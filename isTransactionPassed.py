import constants, os, sys

header    = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;

hashStr = str(sys.argv[1]);
os.environ['hashStr'] = hashStr;
# hashStr = '0xe5c447e2c68fc699bffaccea9832ff693d9d40cf7784d8f3913adf67970b' 
print(constants.contractCall('eBlocBroker.isTransactionPassed(\'$hashStr\')'));
