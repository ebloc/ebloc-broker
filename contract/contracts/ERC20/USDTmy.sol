// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ERC20.sol";
import "./Ownable.sol";
import "./Context.sol";

contract USDTmy is Ownable, ERC20 {
    constructor() ERC20("USDmy", "USDmy") Ownable(msg.sender){
        mint(msg.sender, 1000000000 * (10**uint256(decimals())));
    }

    function mint(address account, uint256 amount) public _onlyOwner {
        _mint(account, amount);
    }

    function burn(address account, uint256 amount) public _onlyOwner {
        _burn(account, amount);
    }

    /* function _distributeTransfer(address to, uint256 amount) internal virtual returns (bool) { */
    /*     _transfer(_owner, to, amount); */
    /*     return true; */
    /* } */

}
