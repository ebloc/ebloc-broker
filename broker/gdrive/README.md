# Installation

link:
https://stackoverflow.com/questions/65396850/how-to-handle-app-is-temporarily-blocked-from-logging-in-with-your-google-accou/65507155#65507155


@tellowkrinkle's [comment][1] help me to solve the issue.


> Probably yes. I have the old binary and Google blocks it from authenticating,
> saying that it's dangerous and they blocked it for my safety (thanks a
> lot). It looks like Google now requires you to let them review applications
> that want to access sensitive information through their API
>
> If you want to use it for yourself, you will need to:
>
> 1. Go to https://console.developers.google.com and create a new project for yourself
> 2. Search for the Google Drive API in the search box at the top, and turn it on
> 3. Click OAuth consent screen on the left and set it up.
>     - Assuming your account isn't part of an organization, you'll have to say your app is for external users and in testing
>     - In the required scopes section, add .../auth/docs and .../auth/drive (I'm not sure which needed, it's probably only one of
> those). This will probably not be available if you didn't complete (2)
>     - Add the accounts you want to use with your copy of gdrive as testers of your app. Only these accounts will be able to use your copy
> of gdrive, so everyone will have to compile their own (unless someone
> goes and gets theirs reviewed by Google)
> 4. Click Credentials on the left, then Create Credentials, then OAuth client ID. The application type is Desktop app
> 5. Copy the Client ID and Secret into handlers_drive.go lines 17 and 18 and compile the application

-------

```
cd ~/
git clone https://github.com/prasmussen/gdrive.git && cd gdrive
```

Copy the Client ID and Secret into handlers_drive.go lines 17 and 18 and compile the application

```
$ emacs -nw handlers_drive.go
```

```
FILE=~/.gdrive/token_v2.json
if [ -f "$FILE" ]; then
	mv ~/.gdrive/token_v2.json ~/.gdrive/token_v2.json.old
fi
go get github.com/prasmussen/gdrive
go build -ldflags "-w -s"
cp gdrive $GOPATH/bin/gdrive
gdrive about
```

Go to the following url in your browser:
https://accounts.google.com/o/oauth2/auth?access_type=.....

Enter verification code:


# Guide

- [TUTORIAL: How to get rid of 403 Errors][2]
- https://github.com/prasmussen/gdrive/issues/426#issuecomment-459150627
- https://github.com/marufshidiq/gdrive-cli-builder
- [stackoverflow Answer](https://stackoverflow.com/a/65507155/2402577)

  [1]: https://github.com/prasmussen/gdrive/commit/31d0829c180795d17e00b7a354fffe4d72be712b#commitcomment-45165924
  [2]: https://github.com/prasmussen/gdrive/issues/426
