// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is Ownable, VRFConsumerBaseV2 {
    VRFCoordinatorV2Interface COORDINATOR;

    // Your subscription ID.
    uint64 s_subscriptionId;

    // Rinkeby coordinator. For other networks,
    // see https://docs.chain.link/docs/vrf-contracts/#configurations
    address vrfCoordinator;

    // The gas lane to use, which specifies the maximum gas price to bump to.
    // For a list of available gas lanes on each network,
    // see https://docs.chain.link/docs/vrf-contracts/#configurations
    bytes32 keyHash =
        0xd89b2bf150e3b9e13446986e571fb9cab24b13cea0a43ea20a6049a85cc807cc;

    // Depends on the number of requested values that you want sent to the
    // fulfillRandomWords() function. Storing each word costs about 20,000 gas,
    // so 100,000 is a safe default for this example contract. Test and adjust
    // this limit based on the network that you select, the size of the request,
    // and the processing of the callback request in the fulfillRandomWords()
    // function.
    uint32 callbackGasLimit = 100000;

    // The default is 3, but you can set this higher.
    uint16 requestConfirmations = 3;

    // For this example, retrieve 1 random value in one request.
    // Cannot exceed VRFCoordinatorV2.MAX_NUM_WORDS.
    uint32 numWords = 1;

    uint256 public s_requestId;

    enum LotteryState {
        Open,
        Closed
    }

    mapping(uint256 => address) public lotteryEntryOwner;
    mapping(address => uint256) public ownerEntryCount;
    mapping(address => uint256) public ownerPrizeAmount;

    uint256 public entryFee = 0.01 * 10**18;
    uint256 public entryCount;
    uint256 public minEntryCount;
    uint256 public poolPrizeAmount;

    LotteryState public state;
    // 	uint public ownerCut;

    uint256 public winnerId;

    event newEntry(address player, uint256 entryNumber);
    event newWinner(address player, uint256 prizeAmount);

    //modifiers
    modifier isState(LotteryState _state) {
        require(state == _state, "Action cannot be performed in this state");
        _;
    }

    //constructor
    constructor(
        address _vrfCoordinator,
        uint256 _minEntryCount,
        uint64 subscriptionId
    ) Ownable() VRFConsumerBaseV2(_vrfCoordinator) {
        require(
            _minEntryCount > 1,
            "Minimum entry count must be greater than 1"
        );
        COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
        vrfCoordinator = _vrfCoordinator;
        s_subscriptionId = subscriptionId;
        minEntryCount = _minEntryCount;
        _changeState(LotteryState.Open);
    }

    //functions
    function submitEntry() public payable isState(LotteryState.Open) {
        require(msg.value == entryFee, "Fixed entry fee amount required");
        require(
            ownerEntryCount[msg.sender] < 1,
            "Only one entry allowed per address"
        );
        entryCount++;
        poolPrizeAmount += msg.value;
        // 		payable(owner()).transfer(ownerCut);
        lotteryEntryOwner[entryCount] = msg.sender;
        ownerEntryCount[msg.sender]++;
        emit newEntry(msg.sender, entryCount);
    }

    function clearVariablesForNewRound() private isState(LotteryState.Closed) {
        for (uint256 i = 1; i <= entryCount; i++) {
            address addressToBeRemoved = lotteryEntryOwner[i];
            delete ownerEntryCount[addressToBeRemoved];
            delete lotteryEntryOwner[i];
        }
        entryCount = 0;
        poolPrizeAmount = 0;
        winnerId = 0;
    }

    function assignWinner() external onlyOwner isState(LotteryState.Open) {
        require(entryCount >= minEntryCount, "Minimum entry count required");
        _changeState(LotteryState.Closed);
        s_requestId = COORDINATOR.requestRandomWords(
            keyHash,
            s_subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
    }

    function fulfillRandomWords(uint256 requestId, uint256[] memory randomness)
        internal
        override
    {
        s_requestId = requestId;
        winnerId = (randomness[0] % entryCount) + 1;
        address winnerAddress = lotteryEntryOwner[winnerId];
        ownerPrizeAmount[winnerAddress] += poolPrizeAmount;
        emit newWinner(winnerAddress, poolPrizeAmount);
        clearVariablesForNewRound();
        _changeState(LotteryState.Open);
    }

    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }

    function _changeState(LotteryState _newState) private {
        state = _newState;
    }

    function withdrawPrizeMoney() public payable {
        require(
            ownerPrizeAmount[msg.sender] > 0,
            "Positive balance required for withdrawal"
        );
        require(ownerPrizeAmount[msg.sender] <= address(this).balance);
        uint256 prizeBalance = ownerPrizeAmount[msg.sender];
        delete ownerPrizeAmount[msg.sender];
        payable(msg.sender).transfer(prizeBalance);
    }
}
