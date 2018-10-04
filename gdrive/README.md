# Load:

```
folderName='ipfs'
clusterToShare='aalimog1@binghamton.edu' //'alper01234alper@gmail.com'

gdrive upload --recursive $folderName
jobKey=$(gdrive list | grep $folderName | awk '{print $1}')
echo jobKey=$jobKey 
gdrive share $jobKey  --role writer --type user --email $clusterToShare
```

---------------

# Save:

```
cd folder
shareId='1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG'

folderName=$(gdrive info $shareId | grep 'Name' | awk '{print $2}')

mimeType=$(gdrive info 1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG | grep 'Mime' | awk '{print $2}')

gdrive download --recursive  $shareId --force

gdrive upload --parent $shareId README.md
gdrive upload --parent --recursive $shareId folder  # upload folder
```
