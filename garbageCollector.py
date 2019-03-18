import os, json, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path

def addElement(data, key, elementToAdd):
    data[key] = elementToAdd    
    
def removeElement(data, elementToRemove):
    for element in list(data):
        if elementToRemove in element:
            del data[elementToRemove]

filePath = os.getenv("LOG_PATH") + '/' + 'cachingRecord.json'
print(filePath)


if not os.path.isfile(filePath):
    data = {}
else:           
    with open(filePath) as data_file:
        data = json.load(data_file)

        
addElement(data, 'jobKey', ['local', 'userName', 'timestamp', 'keepTime'])
addElement(data, 'ipfsHash', 'timestamp')



with open('data.json', 'w') as outfile:
    json.dump(data, outfile)



if 'jobKey' in data:  
    print(data['jobKey'][0])    
    print(data['jobKey'])

removeElement(data, 'ipfsHash')


with open(filePath, 'w') as data_file:
    data = json.dump(data, data_file)
