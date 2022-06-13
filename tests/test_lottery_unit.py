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


def test_can_submit_entry():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    tx = lottery.submitEntry({"from": account, "value": entry_fee})
    tx.wait(1)
    assert lottery.entryCount() > 0
    assert tx.events["newEntry"]["player"] == account.address
    assert lottery.lotteryEntryOwner(1) == account.address


def test_cannot_submit_entry_zero_amount():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.submitEntry({"from": account, "value": 0})


def test_cannot_submit_entry_low_amount():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.submitEntry({"from": account, "value": entry_fee - 10})


def test_cannot_submit_entry_high_amount():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.submitEntry({"from": account, "value": entry_fee + 10})


def test_only_one_entry_per_address():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.submitEntry({"from": account, "value": entry_fee})
    assert lottery.ownerEntryCount(account.address) == 1
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.submitEntry({"from": account, "value": entry_fee})


def test_get_contract_balance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.submitEntry({"from": account, "value": entry_fee})
    assert lottery.getContractBalance() == entry_fee


def test_assign_winner_not_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.submitEntry({"from": account, "value": entry_fee})
    lottery.submitEntry({"from": get_account(index=1), "value": entry_fee})
    lottery.submitEntry({"from": get_account(index=2), "value": entry_fee})
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.assignWinner({"from": get_account(index=1)})


def test_assign_winner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.submitEntry({"from": account, "value": entry_fee})
    lottery.submitEntry({"from": get_account(index=1), "value": entry_fee})
    lottery.submitEntry({"from": get_account(index=2), "value": entry_fee})
    lottery.assignWinner({"from": account})
    coordinator, sub_id = get_vrf_coordinator()
    ff_tx = coordinator.fulfillRandomWords(
        lottery.s_requestId(), lottery.address, {"from": account}
    )
    ff_tx.wait(1)
    assert lottery.winnerId() != 0


# def test_withdraw():
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip()
#     account = get_account()
#     lottery = deploy_lottery()
#     lottery.submitEntry({"from": account, "value": entry_fee})
#     lottery.submitEntry({"from": get_account(index=1), "value": entry_fee})
#     lottery.submitEntry({"from": get_account(index=2), "value": entry_fee})
#     tx = lottery.assignWinner({"from": account})
#     tx.wait(3)
