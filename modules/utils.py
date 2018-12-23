from enum import Enum
from cplex import Cplex
from cplex._internal._constants import CPX_MAX, CPX_MIN
from typing import List
from networkx import coloring, Graph, maximal_independent_set
from time import time
import sys

problem_type = Cplex.problem_type
EPSILON = 0.0001


class OBJECTIVE_SENSE(Enum):
    MAX = CPX_MAX
    MIN = CPX_MIN


class SENSE(Enum):
    GREATER = 'G'
    LOWER = 'L'

    def to_sign(self):
        if self is SENSE.GREATER:
            return '>='
        elif self is SENSE.LOWER:
            return '<='

        return None


class LinearConstraint:
    prefix = 'c'

    def __init__(self, variables: List[str], coefficients: List[float], sense: SENSE, right_side: float):
        self.right_side = right_side
        self.sense = sense
        self.coefficients = coefficients
        self.variables = variables

    def set_to(self, problem: Cplex):
        index = problem.linear_constraints.get_num()
        sense = self.sense.value
        identifier = self.prefix + str(index)

        problem.linear_constraints.add(names=[identifier], lin_expr=[self.get_left_side()], senses=[sense],
                                       rhs=[self.right_side])
        return identifier

    @staticmethod
    def get_node_constraint_name(index: int = None, node: int = None):
        if index is None and node is None:
            raise RuntimeError('No index or node provided')
        if node:
            index = node - 1

        return LinearConstraint.prefix + str(index)

    @staticmethod
    def set_many(problem: Cplex, constraints):
        """

        :param problem: Cplex
        :type constraints: list[LinearConstraint]
        """
        for constraint in constraints:
            constraint.set_to(problem)

    def get_left_side(self):
        return [self.variables, self.coefficients]

    def __str__(self):
        lh = [str(abs(self.coefficients[i])) + str(self.variables[i]) for i in range(0, len(self.variables))]
        left_side = lh[0]

        for i in range(0, len(lh)):
            sign = '+' if self.coefficients[i] >= 0 else '-'
            left_side += ' {0} {1}'.format(sign, lh[i])

        return '{0} {1} {2}'.format(left_side, self.sense.to_sign(), str(self.right_side))


class Objective:
    def __init__(self, variables: List[str], sense: OBJECTIVE_SENSE, type: problem_type, ub: float = None,
                 lb: float = None, var_type: str = None, coefficients: List[float] = None):
        self.variables = variables
        self.coefficients = coefficients if coefficients is not None else [1.0] * len(variables)
        self.type = type
        self.sense = sense
        self.ub = ub
        self.lb = lb
        self.var_type = var_type

    def set_to(self, problem: Cplex):
        problem.set_problem_type(self.type)
        types = [self.var_type] * len(self.variables) if self.var_type is not None else ""
        problem.variables.add(names=self.variables, obj=self.coefficients, types=types)
        problem.objective.set_sense(sense=self.sense.value)

        if self.lb:
            problem.variables.set_lower_bounds([self.lb] * len(self.variables))
        if self.ub:
            problem.variables.set_upper_bounds([self.ub] * len(self.variables))


class TimerState(Enum):
    FINISHED = 'Finished',
    PENDING = 'Pending',
    INITIAL = 'Initial'


class TimerError(RuntimeError):
    pass


class Timer:
    _start_time = None
    _end_time = None
    _state = TimerState.INITIAL

    def start(self):
        if self._state is TimerState.PENDING:
            raise TimerError('Timer is already running')
        elif self._state is TimerState.FINISHED:
            raise TimerError('Timer is finished')

        self._state = TimerState.PENDING
        self._start_time = time() * 1000

    def stop(self):
        if self._state is TimerState.INITIAL:
            raise TimerError('Timer is not started')
        elif self._state is TimerState.FINISHED:
            raise TimerError('Timer is already finished')

        self._state = TimerState.FINISHED
        self._end_time = time() * 1000

    def reset(self):
        self._state = TimerState.INITIAL
        self._start_time = None
        self._end_time = None

    def duration(self):
        if self._state is not TimerState.FINISHED:
            raise TimerError('Timer is not finished')

        return self._end_time - self._start_time


def get_independent_sets(graph):
    independent_sets = []
    strategies = [coloring.strategy_largest_first,
                  coloring.strategy_random_sequential,
                  coloring.strategy_independent_set,
                  coloring.strategy_connected_sequential_bfs,
                  coloring.strategy_connected_sequential_dfs,
                  coloring.strategy_saturation_largest_first]

    for strategy in strategies:
        d = coloring.greedy_color(graph, strategy=strategy)
        for color in set(color for node, color in d.items()):
            independent_sets.append(
                [key for key, value in d.items() if value == color])

    return independent_sets


def find_max_independent_set(independent_sets: List[List[int]], opt_point: List[float]):
    def get_sum(independent_set):
        return sum([opt_point[node - 1] for node in independent_set])

    result = max(independent_sets, key=get_sum)
    return result, get_sum(result)


def is_integer(value: float):
    return abs(value - round(value)) <= EPSILON


def is_one(value: float):
    return abs(value - 1.0) <= EPSILON


def compare(val1: float, val2: float):
    diff = val1 - val2
    if diff > EPSILON:
        return 1
    elif diff < -EPSILON:
        return - 1

    return 0


def build_variables(independent_sets: List[List[int]], prefix: str = 'x'):
    return [prefix + str(x + 1) for x in range(0, len(independent_sets))]


def nonint_items(nodes: List[int], opt_point: List[float]):
    return [node for node in nodes if not is_integer(opt_point[node - 1])]


def get_maximal_independent_set(graph: Graph, opt_point: List[float]):
    nodes = nonint_items(list(graph.nodes), opt_point)

    if not len(nodes):
        return

    sub_graph: Graph = graph.subgraph(nodes)
    independent_sets = get_independent_sets(sub_graph)
    maximal_set, maximal_set_value = find_max_independent_set(independent_sets, opt_point)

    return maximal_independent_set(graph, maximal_set), maximal_set_value


