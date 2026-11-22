import argparse
import csv
import math
from functools import partial
from pathlib import Path

import LiteEFG
from LiteEFG.baselines import DCFR, PCFR, CFRplus

from games import GAMES, POKER, load
from restarting import DEFAULT_THRESHOLD, rcfr_plus, rdcfr, rpcfr_plus

POKER_ITERATIONS = 100_000
OTHER_ITERATIONS = 10_000
RECORD_EVERY_ITERATION_UNTIL = 20
RECORD_RATIO = 10 ** (1 / 30)
TARGET_EXPLOITABILITY = 1e-12
RESULTS = Path(__file__).resolve().parents[1] / "results"

BASELINES = {"CFR+": CFRplus, "DCFR": DCFR, "PCFR+": PCFR}
RESTARTED = {"rCFR+": rcfr_plus, "rPCFR+": rpcfr_plus, "rDCFR": rdcfr}


def checkpoints(iterations):
    dense = min(RECORD_EVERY_ITERATION_UNTIL, iterations)
    points = set(range(1, dense + 1))
    position = float(RECORD_EVERY_ITERATION_UNTIL)
    while position < iterations:
        position *= RECORD_RATIO
        points.add(min(iterations, round(position)))
    points.add(iterations)
    return points


def trace(iterations, step, measure):
    points = checkpoints(iterations)
    curve = []
    for iteration in range(1, iterations + 1):
        step()
        if iteration not in points:
            continue

        cost, exploitability = measure(iteration)
        if math.isinf(exploitability):
            continue

        curve.append((cost, exploitability))
        if exploitability <= TARGET_EXPLOITABILITY:
            break
    return curve


def run_baseline(method, game, iterations):
    environment = LiteEFG.OpenSpielEnv(game)
    graph = method.graph()
    environment.set_graph(graph)
    linear_average = method is not DCFR

    def nash_conv(strategy, mode="default"):
        return sum(environment.exploitability(strategy, mode))

    def step():
        if linear_average:
            environment.update_strategy(graph.current_strategy())
        graph.update_graph(environment)

    def measure(iteration):
        current = graph.current_strategy()
        if linear_average:
            average = nash_conv(current, "linear-avg-iterate")
        else:
            average = nash_conv(graph.avg_strategy)
        return iteration, min(average, nash_conv(current)) / 2

    return trace(iterations, step, measure)


def run_restarted(method, game, iterations):
    solver = method(LiteEFG.OpenSpielEnv(game))

    def measure(iteration):
        return iteration + solver.checks, solver.best_nash_conv / 2

    return trace(iterations, solver.step, measure)


def run_methods(game, iterations):
    curves = {}
    for label, method in BASELINES.items():
        curves[label] = run_baseline(method, game, iterations)
    for label, method in RESTARTED.items():
        curves[label] = run_restarted(method, game, iterations)
    return curves


def run_thresholds(game, iterations, thresholds):
    curves = {}
    for threshold in [DEFAULT_THRESHOLD, *thresholds]:
        method = partial(rdcfr, threshold=threshold)
        label = f"rDCFR threshold={threshold:.2f}"
        curves[label] = run_restarted(method, game, iterations)
    return curves


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", default=",".join(GAMES))
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--thresholds", default="")
    arguments = parser.parse_args()
    arguments.games = arguments.games.split(",")
    thresholds = arguments.thresholds.split(",")
    arguments.thresholds = [float(value) for value in thresholds if value]
    return arguments


def main():
    arguments = parse_arguments()
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "curves.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["game", "method", "iterations", "exploitability"])
        for name in arguments.games:
            game = load(name)
            default = POKER_ITERATIONS if name in POKER else OTHER_ITERATIONS
            iterations = arguments.iterations or default
            if arguments.thresholds:
                curves = run_thresholds(game, iterations, arguments.thresholds)
            else:
                curves = run_methods(game, iterations)

            final = {}
            for label, curve in curves.items():
                writer.writerows([name, label, *point] for point in curve)
                _, last = curve[-1]
                final[label] = f"{last:.0e}"
            print(name, final, flush=True)


if __name__ == "__main__":
    main()
