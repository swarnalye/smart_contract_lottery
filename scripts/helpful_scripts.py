from brownie import network, config, accounts, Contract, interface, VRFCoordinatorV2Mock


FORKED_BLOCKCHAIN = ["mainnet-fork"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_account(index=None, name=None):
    if index:
        return accounts[index]
    if name:
        return accounts.add(config["wallets"][name])
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_BLOCKCHAIN
    ):
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["DEV01"])


def get_vrf_coordinator():
    account = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(VRFCoordinatorV2Mock) <= 0:
            deploy_mock()
        mock_coordinator = VRFCoordinatorV2Mock[-1]
        create_sub_tx = mock_coordinator.createSubscription({"from": account})
        sub_id = create_sub_tx.return_value
        fund_sub_tx = mock_coordinator.fundSubscription(
            sub_id, 10 * 10**18, {"from": account}
        )
        return mock_coordinator, sub_id
    else:
        coordinator = interface.VRFCoordinatorV2Interface(
            config["networks"][network.show_active()]["vrf_coordinator"]
        )
        return (
            coordinator,
            config["networks"][network.show_active()]["coordinator_sub_id"],
        )


def deploy_mock():
    account = get_account()
    VRFCoordinatorV2Mock.deploy(1000000000000, 0.0000001, {"from": account})
    print("Mock contract deployed!")
