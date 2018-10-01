#!/usr/bin/env python

import owncloud, hashlib, getpass
# https://github.com/owncloud/pyocclient/blob/master/owncloud/owncloud.py
# https://github.com/owncloud/pyocclient/issues/199#issuecomment-309497823

#Password read from the file.
f = open( '/home/netlab/pyhton/password.txt', 'r')
password = f.read().rstrip('\n').replace(" ", "")
f.close()

#Password could also entered by the user.
#password = getpass.getpass("Enter your Eudat password:")

oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')
oc.share_file_with_user(name, 'ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu', remote_user=True, perms=31)




# val = oc.accept_remote_share(1195);
# print(val)
# z = oc.list_open_remote_share();

'''
#oc.put_file( "/DfQlm5J42nEGnH7", "/home/alper/alper/run.sh")
#oc.put_file(  "DfQlm5J42nEGnH7", "/home/alper/alper/run.sh")

#k = oc.get_directory_as_zip("https://b2drop.eudat.eu/s/DfQlm5J42nEGnH7", "/home")
#print( k )



print( len(z) )

for i in range(0, len(z) ):
    #print( z[i]  )
    print( z[i]['name'] )
    #oc.decline_remote_share(int)
    #print( z[i]['id'] )
    #print( "Share Token: " + z[i]['share_token'] )
    #print("-----------")
    #oc.decline_remote_share(int(z[i]['id']))


val = oc.accept_remote_share("1195");
#print(val)
#oc.decline_remote_share(68)
#oc.remove 
'''
