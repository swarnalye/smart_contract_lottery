from brownie import Lottery, accounts, config, network, exceptions, convert
from web3 import Web3
from scripts.deploy import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_vrf_coordinator,
)
import pytest
import time

entry_fee = 0.01 * 10**18


def test_all():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.submitEntry({"from": account, "value": entry_fee})
    lottery.submitEntry({"from": get_account(name="DEV02"), "value": entry_fee})
    lottery.submitEntry({"from": get_account(name="DEV03"), "value": entry_fee})
    assert lottery.entryCount() == 3
    lottery.assignWinner({"from": account})
    time.sleep(120)
    assert lottery.winnerId != 0
    if lottery.winnerId() == 1:
        assert lottery.ownerPrizeAmount[account.address] > 0
        lottery.withdrawPrizeMoney({"from": account})
        assert lottery.ownerPrizeAmount[account.address] == 0
    elif lottery.winnerId() == 2:
        assert lottery.ownerPrizeAmount[get_account(name="DEV02").address] > 0
        lottery.withdrawPrizeMoney({"from": get_account(name="DEV02")})
        assert lottery.ownerPrizeAmount[get_account(name="DEV02").address] == 0
    elif lottery.winnerId() == 3:
        assert lottery.ownerPrizeAmount[get_account(name="DEV03").address] > 0
        lottery.withdrawPrizeMoney({"from": get_account(name="DEV03")})
        assert lottery.ownerPrizeAmount[get_account(name="DEV03").address] == 0
