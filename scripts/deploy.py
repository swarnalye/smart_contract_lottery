from brownie import network, config, accounts, Contract, interface, Lottery
from scripts.helpful_scripts import (
    get_account,
    FORKED_BLOCKCHAIN,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_vrf_coordinator,
)


def main():
    account = get_account()
    lottery = deploy_lottery()


def deploy_lottery():
    account = get_account()
    coordinator, sub_id = get_vrf_coordinator()
    lottery = Lottery.deploy(
        coordinator.address,
        2,
        sub_id,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    coordinator.addConsumer(sub_id, lottery.address, {"from": get_account})
    return lottery
