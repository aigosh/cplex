from cplex import Cplex
from docplex.cp.solver import solver
from dimacs import DIMACS
from math import floor

problem_type = Cplex.problem_type


class MaxCliqueSolver:
    __max_clique_len = 0
    __max_clique = []
    __upper_bound = None
    __problem = None
    __heuristics = []
    __optimization_problem = None

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

        self.__init_optimization_problem()

        # print(self.__heuristics)

    def __graph(self):
        return self.__problem.graph()

    def __init_optimization_problem(self):
        problem = Cplex()
        problem.set_problem_type(problem_type.LP)

        sense = problem.objective.sense
        problem.objective.set_sense(sense=sense.maximize)

        variables = self.__build_variables()
        print('Variables:', variables)

        objective = self.__build_objective(variables)
        print('Objective:', objective)

        problem.variables.add(names=variables, obj=objective)

        constraints = self.__build_constraints(variables)
        self.__set_constraints(problem, constraints)

        self.__optimization_problem = problem

    def __build_variables(self):
        return ['x' + str(x) for x in range(1, self.__problem.vertices_num() + 1)]

    def __build_constraints(self, variables):
        constraints = []

        for i in range(0, self.__problem.vertices_num()):
            constraint = [[variables[i]], [1], 'L', 1]
            constraints.append(constraint)
            for j in range(0, self.__problem.vertices_num()):
                if i != j and not self.__graph().has_edge(i, j):
                    constraint = [[variables[i], variables[j]], [1, 1], 'L', 1]
                    constraints.append(constraint)

        return constraints

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

            problem.linear_constraints.add(names=['constraint' + str(i)], lin_expr=[lh], senses=[sign], rhs=[rh])

    def __get_sorted_nodes(self):
        graph = self.__graph()

        return sorted(graph.nodes, key=lambda x: graph.degree[x], reverse=True)

    def __apply_heuristics(self, heuristics):
        result = [heuristic(self.__problem.graph()) for heuristic in heuristics]
        print(result)

        self.__max_clique = max(result, key=len)
        self.__max_clique_len = len(self.__max_clique)

        return self.__max_clique, self.__max_clique_len

    # def __resolve_max_clique(self, clique, candidates):
    #     upper_bound = len(clique) + len(candidates)
    #
    #     if upper_bound < self.__max_clique_len:
    #         return
    #
    #     node = candidates[0]
    #     new_candidates = list(filter(lambda x: self.__graph().has_edge(node, x), candidates[1:]))
    #
    #     for i in range(0, len(new_candidates)):
    #         if upper_bound - i < self.__max_clique_len:
    #             return
    #
    #         self.__resolve_max_clique(clique + [node], new_candidates[i:])

    def solve(self):
        self.__apply_heuristics(self.__heuristics)

        # nodes = self.__get_sorted_nodes()
        # self.__resolve_max_clique([], nodes)

        problem = self.__optimization_problem

        problem.solve()
        opt_point = problem.solution.get_values()
        solution = problem.solution.get_objective_value()

        upper_bound = floor(solution)
        print(solution, upper_bound, opt_point)

        # if upper_bound <= self.__max_clique_len:
        #     return self.__max_clique_len
        #
        # for value in opt_point:
        #     if not value.is_integer():
        #         val = floor(value)

        return self.__max_clique_len
