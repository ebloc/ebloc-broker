require('dotenv').config(); // https://github.com/motdotla/dotenv

module.exports = Object.freeze({
    WHOAMI:      process.env.WHOAMI,
    EBLOCBROKER: process.env.EBLOCPATH,
    LOG_PATH:    process.env.LOG_PATH,
    PROVIDER_ID:  process.env.PROVIDER_ID,
    RPC_PORT:    process.env.RPC_PORT
});
