# Headless Usage & Authorization 

```
$ google-drive-ocamlfuse -headless -label me -id ##yourClientID##.apps.googleusercontent.com -secret ###yoursecret#####
```

https://github.com/astrada/google-drive-ocamlfuse/wiki/Headless-Usage-&-Authorization



Set shared_with_me=true in the config file to have read-only access to all your "Shared with me" files under ./.shared.

```
$ cat ~/.gdfuse/me/config | grep shared_with_me
shared_with_me=true
```


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
