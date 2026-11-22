import math

import LiteEFG
from LiteEFG.baselines import DCFR, PCFR, CFRplus

DEFAULT_THRESHOLD = 1 / math.e
REGRET_FLOOR = 1e-12
CHAKRABARTI = dict(
    threshold=0.5, check_every=100, long_period=math.inf, restart_regrets=False
)


def period_graph(base, weight_exponent):
    class Graph(base.graph):
        def __init__(self):
            super().__init__()
            size = self.action_set_size

            with LiteEFG.backward(is_static=True):
                self.uniform = LiteEFG.const(size, 1 / size)
                self.played = self.uniform.copy()
                self.period_length = LiteEFG.const(1, 0.0)
                self.period_sum = LiteEFG.const(size, 0.0)
                self.period_average = self.uniform.copy()

            with LiteEFG.backward():
                self.period_length.inplace(self.period_length + 1)
                weight = self.period_length ** weight_exponent
                played = weight * self.played * self.reach_prob
                self.period_sum.inplace(self.period_sum + played)
                average = self.period_sum.normalize(
                    p_norm=1.0, ignore_negative=True
                )
                self.period_average.inplace(average)
                self.played.inplace(self.strategy.copy())

    return Graph()


class Restarted:
    def __init__(self, environment, base, weight_exponent, threshold,
                 check_every=None, long_period=0.5, restart_regrets=True):
        self.environment = environment
        self.graph = period_graph(base, weight_exponent)
        self.threshold = threshold
        self.check_every = check_every
        self.long_period = long_period
        self.restart_regrets = restart_regrets
        environment.set_graph(self.graph)

        self.iteration = 0
        self.checks = 0
        self.best_nash_conv = math.inf
        self.restart_nash_conv = self.check(self.graph.uniform)
        self.start_period()

    def start_period(self):
        self.period = 0
        self.next_check = 2

    def check(self, strategy):
        self.checks += 1
        return sum(self.environment.exploitability(strategy, "default"))

    def step(self):
        self.graph.update_graph(self.environment)
        self.iteration += 1
        self.period += 1
        if self.check_every is None:
            due = self.period >= self.next_check
        else:
            due = self.iteration % self.check_every == 0
        if not due:
            return

        self.next_check = 2 * self.period
        nash_conv = self.check(self.graph.period_average)
        self.best_nash_conv = min(self.best_nash_conv, nash_conv)
        improved = nash_conv <= self.threshold * self.restart_nash_conv
        too_long = self.period >= self.long_period * self.iteration
        if improved or too_long:
            self.restart()
            self.restart_nash_conv = nash_conv

    def values(self, player, node):
        return [value for _, value in self.environment.get_value(player, node)]

    def restart(self):
        environment, graph = self.environment, self.graph
        for player in (1, 2):
            sums = self.values(player, graph.period_sum)
            if self.restart_regrets:
                self.move_to_period_average(player, sums)
            zeros = [[0.0] * len(period_sum) for period_sum in sums]
            environment.set_value(player, graph.period_sum, zeros)
            lengths = [[0.0] for _ in sums]
            environment.set_value(player, graph.period_length, lengths)
        self.start_period()

    def move_to_period_average(self, player, sums):
        environment, graph = self.environment, self.graph
        regrets = self.values(player, graph.regret_buffer)
        strategies = self.values(player, graph.strategy)
        for infoset, period_sum in enumerate(sums):
            total = sum(period_sum)
            if total <= 0:
                continue

            average = [value / total for value in period_sum]
            positive = sum(max(regret, 0.0) for regret in regrets[infoset])
            mass = max(positive, REGRET_FLOOR)
            regrets[infoset] = [mass * value for value in average]
            strategies[infoset] = average

        environment.set_value(player, graph.regret_buffer, regrets)
        environment.set_value(player, graph.strategy, strategies)
        environment.set_value(player, graph.played, strategies)


def rdcfr(environment, threshold=DEFAULT_THRESHOLD):
    return Restarted(
        environment, DCFR, weight_exponent=1.0, threshold=threshold
    )


def rcfr_plus(environment):
    return Restarted(
        environment, CFRplus, weight_exponent=1.0, **CHAKRABARTI
    )


def rpcfr_plus(environment):
    return Restarted(
        environment, PCFR, weight_exponent=2.0, **CHAKRABARTI
    )
