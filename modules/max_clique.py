from cplex import Cplex
from dimacs import DIMACS
from math import floor
from time import time
from networkx import coloring, Graph, maximal_independent_set
import sys
from enum import Enum

problem_type = Cplex.problem_type
EPSILON = 0.0001


class SENSE(Enum):
    GREATER = 'G',
    LOWER = 'L'


class MaxCliqueSolver:
    __max_clique_len = 0
    __max_clique = []
    __problem = None
    __heuristics = []
    __optimization_problem = None
    __silent = False
    __independent_sets = []

    def __init__(self, problem, heuristics=None):
        """

        :type heuristics: list
        :type problem: DIMACS
        """

        if heuristics is None:
            heuristics = []

        self.__heuristics = heuristics
        self.__problem = problem

    def __graph(self):
        return self.__problem.graph()

    def __init_optimization_problem(self):

        problem = Cplex()

        sense = problem.objective.sense
        problem.objective.set_sense(sense=sense.maximize)

        variables = self.__build_variables()
        # self.__log('Variables: ', variables)

        objective = self.__build_objective(variables)
        # self.__log('Objective: ', objective)

        problem.variables.add(names=variables, types=['C'] * len(variables), ub=[1.0] * self.__problem.vertices_num(),
                              obj=objective)

        constraints = self.__build_constraints(variables)
        # self.__log('Constraints count: ', len(constraints))
        self.__set_constraints(problem, constraints)

        self.__optimization_problem = problem

    def __get_independent_sets(self, graph):
        independent_sets = []
        strategies = [coloring.strategy_largest_first,
                      coloring.strategy_random_sequential,
                      coloring.strategy_independent_set,
                      coloring.strategy_connected_sequential_bfs,
                      coloring.strategy_connected_sequential_dfs,
                      coloring.strategy_saturation_largest_first]

        for strategy in strategies:
            d = coloring.greedy_color(self.__graph(), strategy=strategy)
            for color in set(color for node, color in d.items()):
                independent_sets.append(
                    [key for key, value in d.items() if value == color])

        return independent_sets

    def __init_independent_sets(self):
        graph = self.__graph()
        self.__independent_sets = self.__get_independent_sets(graph)
        # pass

    def __build_indepndent_set_constraint(self, variables, independent_set):
        constraint_variables = [variables[node - 1] for node in independent_set]
        return [constraint_variables, [1.0] * len(constraint_variables), SENSE.LOWER, 1.0]

    def __get_independent_set_constraints(self, variables, independent_sets):
        return [self.__build_indepndent_set_constraint(variables, independent_set)
                for independent_set in independent_sets]

    def __build_variables(self):
        return ['x' + str(x + 1) for x in range(0, self.__problem.vertices_num())]

    def __build_constraints(self, variables):
        constraints = []

        for i in range(0, self.__problem.vertices_num()):
            for j in range(i, self.__problem.vertices_num()):
                if i != j and not self.__graph().has_edge(i + 1, j + 1):
                    constraint = [[variables[i], variables[j]], [1.0, 1.0], SENSE.LOWER, 1.0]
                    # self.__log('Constraint: ', constraint)
                    constraints.append(constraint)

        independent_set_constraints = self.__get_independent_set_constraints(variables, self.__independent_sets)
        constraints.extend(independent_set_constraints)

        return constraints

    def __get_max_independent_set(self, independent_sets, opt_point):
        def get_sum(independent_set):
            return sum([opt_point[node - 1] for node in independent_set])

        result = max(independent_sets, key=get_sum)
        return result, get_sum(result)

    def __is_integer(self, value):
        return abs(value - round(value)) <= EPSILON

    def __build_objective(self, variables):
        objective = [1.0] * len(variables)

        return objective

    def __set_constraints(self, problem, constraints):
        for i in range(0, len(constraints)):
            constraint = constraints[i]

            variables = constraint[0]
            X = constraint[1]

            lh = [variables, X]  # левая часть ограничения
            sign = constraint[2]  # знак
            rh = constraint[3]  # правая часть ограничения

            problem.linear_constraints.add(names=[''.join(variables) + sign + str(rh)], lin_expr=[lh], senses=[sign],
                                           rhs=[rh])

    def __get_sorted_nodes(self):
        graph = self.__graph()

        return sorted(graph.nodes, key=lambda x: graph.degree[x])

    def __apply_heuristics(self, heuristics, nodes):
        result = [heuristic(self.__problem.graph(), nodes) for heuristic in heuristics]
        # self.__log(result)

        self.__max_clique = max(result, key=len)
        self.__max_clique_len = len(self.__max_clique)

        return self.__max_clique, self.__max_clique_len

    def __filter_nodes(self, nodes, degree):
        graph = self.__graph()
        return list(filter(lambda node: graph.degree[node] > degree, nodes))

    def __update_max_clique(self, opt_point):
        clique = []

        # self.__log(opt_point)
        for i in range(0, len(opt_point)):
            if not self.__is_integer(opt_point[i]):
                return False
            if abs(opt_point[i] - 1.0) <= EPSILON:
                clique.append(i + 1)

        self.__max_clique = clique
        self.__max_clique_len = len(clique)

        self.__log('\n* Maximum clique updated: ', self.__max_clique_len, force=True)

        return True

    def __nonint_nodes(self, nodes, opt_point):
        return [node for node in nodes if not self.__is_integer(opt_point[node - 1])]

    def __branching(self, problem, nodes):
        """

        :type problem: Cplex
        """
        try:
            problem.solve()
        except:
            return

        opt_point = problem.solution.get_values()
        solution = problem.solution.get_objective_value()

        upper_bound = floor(solution + EPSILON)

        # self.__log(solution, upper_bound, opt_point, )
        # self.__log(upper_bound, self.__max_clique_len, force=True)
        # self.__log('nodes', nodes, force=True)
        # self.__log('opt_point', opt_point, force=True)
        # self.__log('solution', solution, force=True)
        # self.__log('Max clique: ', self.__max_clique, force=True)
        # self.__log('Max clique length: ', self.__max_clique_len, force=True)
        # self.__log('__nodes: ', len(self.__nodes), force=True)
        if upper_bound <= self.__max_clique_len:
            return

        if self.__update_max_clique(opt_point):
            return

        branching = self.__get_branching_node(nodes, opt_point)
        variables = problem.variables.get_names()

        if branching is None:
            return

        branching_node, branch_index, branch_value = branching
        nonint_nodes = self.__nonint_nodes(nodes, opt_point)

        if not len(nonint_nodes):
            return

        sub_graph: Graph = self.__graph().subgraph(nonint_nodes)
        independent_sets = self.__get_independent_sets(sub_graph)

        if len(independent_sets):
            found_independent_set, found_sum = self.__get_max_independent_set(independent_sets, opt_point)

            if found_sum < 1.0:
                return

            max_independent_set = maximal_independent_set(self.__graph(), found_independent_set)
            constraints = self.__get_independent_set_constraints(variables, [max_independent_set])
            self.__set_constraints(problem, constraints)
            self.__branching(problem, nodes)
            return

        variables = problem.variables.get_names()
        variable = variables[branch_index]

        problem.linear_constraints.add(names=[str(variable)],
                                       lin_expr=[[[variable], [1.0]]],
                                       senses=[SENSE.LOWER],
                                       rhs=[0.0])
        self.__log(variable, '>=', branch_value + 1)

        self.__branching(problem, nodes)

        if upper_bound <= self.__max_clique_len:
            return

        problem.linear_constraints.delete(str(variable))

        problem.linear_constraints.add(names=[variable],
                                       lin_expr=[[[variable], [1.0]]],
                                       senses=[SENSE.GREATER],
                                       rhs=[1.0])
        self.__log(variable, '<=', branch_value)

        self.__branching(problem, nodes)
        problem.linear_constraints.delete(str(variable))

    def __get_branching_node(self, nodes, opt_point):
        """

        :type nodes: list
        """
        for node in nodes:
            index = node - 1
            value = opt_point[index]
            if not self.__is_integer(value):
                return node, index, value

    def __configure_problem(self, problem):
        """

        :type problem: Cplex
        """
        if self.__silent:
            problem.set_log_stream(None)
            problem.set_warning_stream(None)
            problem.set_error_stream(None)
            problem.set_results_stream(None)

    def __log(self, *strings, force=False):
        if not self.__silent or force:
            print(*strings)

    def solve(self, silent=False):
        self.__silent = silent
        if not self.__optimization_problem:
            self.__init_independent_sets()
            self.__init_optimization_problem()
            self.__configure_problem(self.__optimization_problem)

        nodes = self.__get_sorted_nodes()

        self.__apply_heuristics(self.__heuristics, nodes)
        self.__log('* Heuristics clique: ', self.__max_clique_len, force=True)

        nodes = self.__filter_nodes(nodes, self.__max_clique_len)

        start_time = time() * 1000
        # self.__log('Start time: ', start_time)

        try:
            self.__branching(self.__optimization_problem, nodes)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            self.__log("Unexpected error:", sys.exc_info()[0], force=True)
            # pass

        # self.__pool.join()
        end_time = time() * 1000
        # self.__log(end_time)

        duration = end_time - start_time

        return self.__max_clique, self.__max_clique_len, duration
