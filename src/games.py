import pyspiel

DECK = dict(
    numPlayers=2, numRounds=2, blind="1 1", firstPlayer="1 1",
    numSuits=2, numRanks=3, numHoleCards=1, numBoardCards="0 1",
)
LEDUC = DECK | dict(betting="limit", raiseSize="2 4", maxRaises="2 2")
NO_LIMIT = DECK | dict(betting="nolimit", bettingAbstraction="fcpa")
RIVER = dict(
    numPlayers=2, numRounds=1, blind="1 1", firstPlayer="1",
    numSuits=4, numHoleCards=2, numBoardCards="5",
    betting="nolimit", bettingAbstraction="fcpa", potSize=20, stack="40 40",
)
GOOFSPIEL = dict(imp_info=True, points_order="descending")
BATTLESHIP = dict(
    board_height=2, ship_sizes="[2]", ship_values="[2.0]",
    num_shots=3, allow_repeated_shots=False, loss_multiplier=1.0,
)
OSHI_ZUMO = dict(size=1, min_bid=0)

POKER = {
    "kuhn": (
        "kuhn_poker",
        {},
    ),
    "leduc": (
        "leduc_poker",
        {},
    ),
    "nl_leduc": (
        "universal_poker",
        NO_LIMIT | dict(stack="10 10"),
    ),
    "leduc_5_r3": (
        "universal_poker",
        LEDUC | dict(numRanks=5, maxRaises="3 3"),
    ),
    "river_9": (
        "universal_poker",
        RIVER | dict(numRanks=8, boardCards="9h8h6c6h2s"),
    ),
    "river_j": (
        "universal_poker",
        RIVER | dict(numRanks=10, boardCards="JdTh8s3c2d"),
    ),
    "river_q": (
        "universal_poker",
        RIVER | dict(numRanks=11, boardCards="QhTh9c8h3s"),
    ),
    "leduc_13": (
        "universal_poker",
        LEDUC | dict(numRanks=13),
    ),
    "nl_leduc_13": (
        "universal_poker",
        NO_LIMIT | dict(numRanks=13, stack="20 20"),
    ),
    "leduc_13_r3": (
        "universal_poker",
        LEDUC | dict(numRanks=13, maxRaises="3 3"),
    ),
    "leduc_13_4suits": (
        "universal_poker",
        LEDUC | dict(numRanks=13, numSuits=4),
    ),
    "board2_13": (
        "universal_poker",
        LEDUC | dict(numRanks=13, numBoardCards="0 2"),
    ),
}
OTHER = {
    "liars_dice_4": (
        "liars_dice",
        dict(numdice=1, dice_sides=4),
    ),
    "liars_dice_2x3": (
        "liars_dice",
        dict(numdice=2, dice_sides=3),
    ),
    "liars_dice_7": (
        "liars_dice",
        dict(numdice=1, dice_sides=7),
    ),
    "goofspiel_4": (
        "goofspiel",
        GOOFSPIEL | dict(num_cards=4),
    ),
    "goofspiel_6": (
        "goofspiel",
        GOOFSPIEL | dict(num_cards=6),
    ),
    "goofspiel_5_random": (
        "goofspiel",
        GOOFSPIEL | dict(num_cards=5, points_order="random"),
    ),
    "battleship_2x3": (
        "battleship",
        BATTLESHIP | dict(board_width=3),
    ),
    "battleship_2x4_2shots": (
        "battleship",
        BATTLESHIP | dict(board_width=4, num_shots=2),
    ),
    "oshi_zumo_4": (
        "oshi_zumo",
        OSHI_ZUMO | dict(coins=4, horizon=4),
    ),
    "oshi_zumo_6": (
        "oshi_zumo",
        OSHI_ZUMO | dict(coins=6, horizon=6),
    ),
    "biased_rps": (
        "matrix_brps",
        {},
    ),
    "blotto_10_3": (
        "blotto",
        dict(coins=10, fields=3),
    ),
}
GAMES = POKER | OTHER


def load(name):
    game = pyspiel.load_game(*GAMES[name])
    if game.get_type().dynamics == pyspiel.GameType.Dynamics.SIMULTANEOUS:
        return pyspiel.load_game_as_turn_based(*GAMES[name])
    return game
