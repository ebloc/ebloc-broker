Installing Gdrive
=================

-  https://console.cloud.google.com/apis/credentials
-  https://stackoverflow.com/questions/65396850/how-to-handle-app-is-temporarily-blocked-from-logging-in-with-your-google-accou/65507155#65507155

@tellowkrinkle’s
`comment <https://github.com/prasmussen/gdrive/commit/31d0829c180795d17e00b7a354fffe4d72be712b#commitcomment-45165924>`__
help me to solve the issue:

   Probably yes. I have the old binary and Google blocks it from
   authenticating, saying that it’s dangerous and they blocked it for my
   safety (thanks a lot). It looks like Google now requires you to let
   them review applications that want to access sensitive information
   through their API

..

   If you want to use it for yourself, you will need to:

.. code:: markdown

   > Doo

   1. Go to https://console.developers.google.com and create a new project for yourself
   2. Search for the **Google Drive API** in the search box at the top, and click manage this app
   3. Click `OAuth` consent screen on the left and set it up.
       - Assuming your account isn't part of an organization, you'll have to say your app is for external users and in testing
       - In the required scopes section, add **.../auth/docs** and **.../auth/drive** (I'm not sure which needed, it's probably only one of those). This will probably not be available if you didn't complete (2)
       - Add the accounts you want to use with your copy of gdrive as testers of your app. Only these accounts will be able to use your copy
   of gdrive, so everyone will have to compile their own (unless someone
   goes and gets theirs reviewed by Google)
   4. Click Credentials on the left, then Create Credentials, then OAuth client ID. The application type is Desktop app
   5. Copy the Client ID and Secret into handlers_drive.go lines 17 and 18 and compile the application

.. code:: bash

   mkdir -p ~/git
   cd ~/git
   git clone https://github.com/prasmussen/gdrive.git && cd gdrive

Copy the ``Client ID`` and ``Secret`` into ``handlers_drive.go`` lines
17 and 18 and compile the application

**Note:** Generated token expires in 7 days.

Finally: \* https://console.cloud.google.com/apis/credentials/consent
``PUBLISH APP``

.. code:: bash

   $ emacs -nw handlers_drive.go

Build
-----

Open terminal and go to the folder where the ``handerls_drive.go`` is.

.. code:: bash

   rm -f ~/.gdrive/token_v2.json  # delete the old token
   go env -w GO111MODULE=auto
   go get github.com/prasmussen/gdrive  # go install github.com/prasmussen/gdrive@latest
   go build -ldflags "-w -s"
   sudo cp gdrive /usr/local/bin/gdrive
   ./gdrive about

Go to the following url in your browser:
https://accounts.google.com/o/oauth2/auth?access_type=…

``Enter verification code:``

Guide
-----

-  `How to handle “App is temporarily blocked from logging in with your
   Google account”
   barrier <https://stackoverflow.com/a/65507155/2402577>`__
-  `TUTORIAL: How to get rid of 403
   Errors <https://github.com/prasmussen/gdrive/issues/426>`__
-  https://github.com/prasmussen/gdrive/issues/426#issuecomment-459150627
-  https://github.com/marufshidiq/gdrive-cli-builder
-  https://github.com/prasmussen/gdrive/commit/31d0829c180795d17e00b7a354fffe4d72be712b#commitcomment-45165924

Headless Usage & Authorization
------------------------------

.. code:: bash

   $ google-drive-ocamlfuse -headless -label me -id  ##your_client_id##.apps.googleusercontent.com -secret ###yoursecret#####

`doc <https://github.com/astrada/google-drive-ocamlfuse/wiki/Headless-Usage-&-Authorization>`__

Set ``shared_with_me=true`` in the config file to have read-only access
to all your :sub:`“Shared with me”` files under ``./.shared``.

.. code:: bash

   $ cat ~/.gdfuse/me/config | grep shared_with_me
   shared_with_me=true

Load:
-----

.. code:: bash

   folder_name='ipfs'
   provider_to_share='aalimog1@binghamton.edu' //'alper01234alper@gmail.com'
   gdrive upload --recursive $folder_name
   key=$(gdrive list | grep $folder_name | awk '{print $1}')
   echo "key="$key
   gdrive share $key  --role writer --type user --email $provider_to_share

--------------

Save
----

.. code:: bash

   cd folder
   shareId='1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG'
   folder_name=$(gdrive info $shareId | grep 'Name' | awk '{print $2}')
   mimeType=$(gdrive info 1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG | grep 'Mime' | awk '{print $2}')
   gdrive download --recursive  $shareId --force
   gdrive upload --parent $shareId README.md
   gdrive upload --parent --recursive $shareId folder  # upload folder

\*\* TODO:

-  `Google Cloud: OAuth clients in test mode that are using the OAuth
   OOB
   flow <https://github.com/prasmussen/gdrive/issues/621#issuecomment-1184700808>`__
   solution forked: https://github.com/msfjarvis/gdrive
