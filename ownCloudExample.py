#!/usr/bin/env python

import owncloud, hashlib, getpass
#https://github.com/owncloud/pyocclient/blob/master/owncloud/owncloud.py

#Password read from the file.
f = open( '/home/netlab/pyhton/password.txt', 'r')
password = f.read().rstrip('\n').replace(" ", "")
f.close()

#Password could also entered by the user.
#password = getpass.getpass("Enter your Eudat password:")

oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('aalimog1@binghamton.edu', password ); 

#oc.mkdir("helloo")
oc.share_file_with_user( 'helloWorld', '3d8e2dc2-b855-1036-807f-9dbd8c6b1579@b2drop.eudat.eu', remote_user=True )

#oc.share_file_with_user( "hello", "3d8e2dc2-b855-1036-807f-9dbd8c6b1579@b2drop.eudat.eu")

'''
z = oc.list_open_remote_share();

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


#val = oc.accept_remote_share("163");
#print(val)
#oc.decline_remote_share(68)
#oc.remove 
'''
