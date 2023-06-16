[Ethereum Network Intelligence API](https://github.com/cubedro/eth-net-intelligence-api)

> This is the backend service which runs along with ethereum and tracks the network status, fetches information through JSON-RPC and connects through WebSockets to [eth-netstats](https://github.com/cubedro/eth-netstats) to feed information. For full install instructions please read the [wiki](https://github.com/ethereum/wiki/wiki/Network-Status).

If you want to see the status of your node on http://ebloc.cmpe.boun.edu.tr:3001 please do the following:

**To install `npm`: first we have to install `nodejs` and than `npm`:**

For macOS download from following link: https://nodejs.org/en/, download 7.5.0 Current.

`sudo npm install npm -g`

For Linux:

To install Node.js, type the following command in your terminal: `sudo apt-get install nodejs`

Then install the Node package manager, npm: `sudo apt-get install npm`

Create a symbolic link for node, as many Node.js tools use this name to execute.
`sudo ln -s /usr/bin/nodejs /usr/bin/node`

Now we should have both the Node and npm commands working:

```
$ node -v
v0.10.25
$ npm -v
1.3.10
```
**To install Ethereum Network Intelligence API:**

```
git clone https://github.com/cubedro/eth-net-intelligence-api
cd eth-net-intelligence-api
my_path="$PWD";
sudo npm install pm2 -g
npm install
```
`/Users/user_name/.npm-packages/bin/pm2 -> /Users/alper/.npm-packages/lib/node_modules/pm2/bin/pm2`

This should work now: Please note that each user will have its own path for `pm2`.
` /Users/user_name/.npm-packages/bin/pm2 `

For some users only `pm2` may work.

To update pm2:
`/Users/user_name/.npm-packages/bin/pm2 update`

Required for macOS users.
```
sudo mkdir /opt/.pm2
sudo chmod -R 777 /opt/.pm2
```

**To Run:**

You should do this every time you open your computer.

Write your unique name instead of "mynameis". Please note that you can run following command on any path you are in.

```
sudo INSTANCE_NAME=mynameis RPC_HOST=localhost WS_SERVER=http://79.123.177.145:3001 WS_SECRET=63r98c3uz0cyg68v RPC_PORT=8545 LISTENING_PORT=3000 /Users/user_name/.npm-packages/bin/pm2 start $my_path/app.js
```
Following line should return some output starting with `"status            online"`.
`/Users/user_name/.npm-packages/bin/pm2 show app`

Now, you should see your node on http://ebloc.cmpe.boun.edu.tr:3001

If you are connected following peer# cell should show `1`.
<img width="884" alt="screen shot 2017-02-21 at 12 35 35" src="https://cloud.githubusercontent.com/assets/18537398/23159009/e117c500-f829-11e6-9eb9-70870da9c65f.png">
