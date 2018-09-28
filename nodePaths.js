require('dotenv').config(); // https://github.com/motdotla/dotenv

module.exports = Object.freeze({
    WHOAMI:      process.env.WHOAMI,
    EBLOCBROKER: process.env.EBLOCPATH,
    LOG_PATH:    process.env.LOG_PATH,
    CLUSTER_ID:  process.env.CLUSTER_ID,
    RPC_PORT:    process.env.RPC_PORT
});

