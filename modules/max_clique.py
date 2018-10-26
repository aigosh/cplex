from cplex import Cplex
from dimacs import DIMACS
from math import floor
from time import time
import sys

problem_type = Cplex.problem_type


class MaxCliqueSolver:
    __max_clique_len = 0
    __max_clique = []
    __upper_bound = None
    __problem = None
    __heuristics = []
    __optimization_problem = None
    __silent = False
    __nodes = []

    def __init__(self, problem, heuristics=None):
        """

        :type heuristics: list
        :type problem: DIMACS
        """

        if heuristics is None:
            heuristics = []

        self.__heuristics = heuristics
        self.__problem = problem
        self.__upper_bound = problem.vertices_num()

    def __graph(self):
        return self.__problem.graph()

    def __init_optimization_problem(self):

        problem = Cplex()
        problem.set_problem_type(problem_type.LP)

        sense = problem.objective.sense
        problem.objective.set_sense(sense=sense.maximize)

        variables = self.__build_variables()
        self.__log('Variables: ', variables)

        objective = self.__build_objective(variables)
        self.__log('Objective: ', objective)

        problem.variables.add(names=variables, obj=objective)

        constraints = self.__build_constraints(variables)
        self.__log('Constraints count: ', len(constraints))
        self.__set_constraints(problem, constraints)

        self.__optimization_problem = problem

    def __build_variables(self):
        return ['x' + str(x) for x in range(1, self.__problem.vertices_num() + 1)]

    def __build_constraints(self, variables):
        constraints = []

        for i in range(0, self.__problem.vertices_num()):
            constraint = [[variables[i]], [1], 'L', 1]
            constraints.append(constraint)
            for j in range(i, self.__problem.vertices_num()):
                if i != j and not self.__graph().has_edge(i, j):
                    constraint = [[variables[i], variables[j]], [1, 1], 'L', 1]
                    self.__log('Constraint: ', constraint)
                    constraints.append(constraint)

        return constraints

    def __is_integer(self, value):
        return abs(value - round(value)) < 0.0001

    def __build_objective(self, variables):
        objective = [1] * len(variables)

        return objective

    def __set_constraints(self, problem, constraints):
        for i in range(0, len(constraints)):
            constraint = constraints[i]

            variables = constraint[0]
            X = constraint[1]

            lh = [variables, X]  # левая часть ограничения
            sign = constraint[2]  # знак
            rh = constraint[3]  # правая часть ограничения

            problem.linear_constraints.add(names=[str(time())], lin_expr=[lh], senses=[sign], rhs=[rh])

    def __get_sorted_nodes(self):
        graph = self.__graph()

        return sorted(graph.nodes, key=lambda x: graph.degree[x], reverse=True)

    def __apply_heuristics(self, heuristics):
        result = [heuristic(self.__problem.graph(), self.__nodes) for heuristic in heuristics]
        self.__log(result)

        self.__max_clique = max(result, key=len)
        self.__max_clique_len = len(self.__max_clique)

        return self.__max_clique, self.__max_clique_len

    def __filter_nodes(self, degree):
        graph = self.__graph()
        self.__nodes = list(filter(lambda node: graph.degree[node] > degree, self.__nodes))

    def __update_max_clique(self, opt_point):
        clique = []

        self.__log(opt_point)
        for i in range(0, len(opt_point)):
            if not self.__is_integer(opt_point[i]):
                return False
            if opt_point[i] == 1:
                clique.append(i)

        self.__max_clique = clique
        self.__max_clique_len = len(clique)

        return True

    def __resolve_max_clique(self, problem, nodes):
        """

        :type problem: Cplex
        """
        problem.solve()

        opt_point = problem.solution.get_values()
        solution = problem.solution.get_objective_value()

        upper_bound = floor(solution)
        self.__log(solution, upper_bound, opt_point, )

        self.__log(upper_bound, self.__max_clique_len, force=True)
        self.__log('nodes', nodes, force=True)
        self.__log('opt_point', opt_point, force=True)
        self.__log('solution', solution, force=True)
        # self.__log('Max clique: ', self.__max_clique, force=True)
        # self.__log('Max clique length: ', self.__max_clique_len, force=True)
        self.__log('__nodes: ', len(self.__nodes), force=True)
        if upper_bound <= self.__max_clique_len:
            return

        if self.__update_max_clique(opt_point):
            self.__filter_nodes(self.__max_clique_len)
            return

        for i in range(0, len(nodes)):
            node = nodes[i]
            index = node - 1
            value = opt_point[index]
            if not self.__is_integer(value):
                val = floor(value)

                new_nodes = nodes[i + 1:]

                if len(new_nodes) == 0:
                    return

                variables = problem.variables.get_names()
                variable = variables[index]

                new_problem = self.__clone_problem(problem)
                new_problem.linear_constraints.add(names=[str(variable)],
                                                   lin_expr=[[[variable], [1]]],
                                                   senses=['G'],
                                                   rhs=[val + 1])
                try:
                    self.__resolve_max_clique(new_problem, new_nodes)
                except:
                    self.__log("Unexpected error:", sys.exc_info()[0], force=True)

                    new_problem = self.__clone_problem(problem)
                    new_problem.linear_constraints.add(names=[variable],
                                                       lin_expr=[[[variable], [1]]],
                                                       senses=['L'],
                                                       rhs=[val])
                    try:
                        self.__resolve_max_clique(new_problem, new_nodes)
                    except:
                        self.__log("Unexpected error:", sys.exc_info()[0], force=True)

        self.__log('Max clique: ', self.__max_clique, force=True)
        self.__log('Max clique length: ', self.__max_clique_len, force=True)
        self.__log('__nodes: ', len(self.__nodes), force=True)

    def __configure_problem(self, problem):
        """

        :type problem: Cplex
        """
        if self.__silent:
            problem.set_log_stream(None)
            problem.set_warning_stream(None)
            problem.set_error_stream(None)
            problem.set_results_stream(None)

    def __clone_problem(self, problem):
        """

        :type problem: Cplex
        """
        new_problem = Cplex()

        new_problem.set_problem_type(problem.get_problem_type())
        new_problem.objective.set_sense(problem.objective.get_sense())
        new_problem.variables.add(names=problem.variables.get_names(), obj=problem.objective.get_linear())
        new_problem.linear_constraints.add(lin_expr=problem.linear_constraints.get_rows(),
                                           names=problem.linear_constraints.get_names(),
                                           rhs=problem.linear_constraints.get_rhs(),
                                           senses=problem.linear_constraints.get_senses())
        self.__configure_problem(new_problem)

        return new_problem

    def __log(self, *strings, force=False):
        if not self.__silent or force:
            print(*strings)

    def solve(self, silent=False):
        self.__silent = silent
        if not self.__optimization_problem:
            self.__init_optimization_problem()
            self.__configure_problem(self.__optimization_problem)

        self.__nodes = self.__get_sorted_nodes()
        self.__apply_heuristics(self.__heuristics)

        self.__filter_nodes(self.__max_clique_len)

        start_time = time()
        self.__log('Start time: ', start_time)

        try:
            self.__resolve_max_clique(self.__optimization_problem, self.__nodes)
        except:
            self.__log("Unexpected error:", sys.exc_info()[0], force=True)

        end_time = time()
        self.__log(end_time)

        duration = end_time - start_time

        return self.__max_clique, self.__max_clique_len, duration
