import argparse
import time

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, hstack

from games import GAMES, load

TIME_LIMIT = 1800


def sequence_form(game):
    infosets = [{}, {}]
    sizes = [1, 1]
    leaves = []

    def walk(state, sequences, chance):
        if state.is_terminal():
            leaves.append((*sequences, chance * state.returns()[0]))
        elif state.is_chance_node():
            for action, probability in state.chance_outcomes():
                walk(state.child(action), sequences, chance * probability)
        else:
            player = state.current_player()
            key = state.information_state_string(player)
            actions = state.legal_actions()
            if key not in infosets[player]:
                offset = sizes[player]
                children = range(offset, offset + len(actions))
                infosets[player][key] = (sequences[player], children)
                sizes[player] += len(actions)

            _, children = infosets[player][key]
            for action, sequence in zip(actions, children):
                child = list(sequences)
                child[player] = sequence
                walk(state.child(action), child, chance)

    walk(game.new_initial_state(), [0, 0], 1.0)
    rows, columns, payoffs = zip(*leaves)
    payoff = coo_matrix((payoffs, (rows, columns)), shape=sizes)
    return infosets, payoff.tocsr()


def constraints(infosets, size):
    rows, columns, values = [0], [0], [1.0]
    for row, (parent, children) in enumerate(infosets.values(), 1):
        rows += [row] * (len(children) + 1)
        columns += [parent, *children]
        values += [-1.0] + [1.0] * len(children)
    shape = (len(infosets) + 1, size)
    return coo_matrix((values, (rows, columns)), shape=shape)


def solve(infosets, payoff):
    first_size, second_size = payoff.shape
    first_constraints = constraints(infosets[0], first_size)
    second_constraints = constraints(infosets[1], second_size)
    first_rows = first_constraints.shape[0]
    second_rows = second_constraints.shape[0]

    cost = np.zeros(first_size + second_rows)
    cost[first_size] = -1.0
    root = np.zeros(first_rows)
    root[0] = 1.0
    padding = coo_matrix((first_rows, second_rows))
    result = linprog(
        cost,
        A_ub=hstack([-payoff.T, second_constraints.T]),
        b_ub=np.zeros(second_size),
        A_eq=hstack([first_constraints, padding]),
        b_eq=root,
        bounds=[(0, None)] * first_size + [(None, None)] * second_rows,
        method="highs-ds",
        options=dict(presolve=False, time_limit=TIME_LIMIT),
    )
    if result.status == 1:
        return None
    if result.status != 0:
        raise RuntimeError(result.message)
    return result.x[:first_size], -result.ineqlin.marginals


def best_response(infosets, values, pick):
    for parent, children in reversed(infosets.values()):
        values[parent] += pick(values[list(children)])
    return values[0]


def exploitability(infosets, payoff, first_plan, second_plan):
    first = best_response(infosets[0], payoff @ second_plan, np.max)
    second = best_response(infosets[1], payoff.T @ first_plan, np.min)
    return (first - second) / 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", default=",".join(GAMES))
    for name in parser.parse_args().games.split(","):
        start = time.time()
        infosets, payoff = sequence_form(load(name))
        built = time.time()
        plans = solve(infosets, payoff)
        solved = time.time()

        outcome = "time limit"
        if plans is not None:
            outcome = exploitability(infosets, payoff, *plans)
        build_seconds = round(built - start, 2)
        solve_seconds = round(solved - built, 2)
        print(name, build_seconds, solve_seconds, outcome, flush=True)


if __name__ == "__main__":
    main()
