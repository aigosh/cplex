from cplex import Cplex
from dimacs import DIMACS


class MaxCliqueSolver:
    __max_clique_len = 0
    __max_clique = []
    __upper_bound = None
    __problem = None
    __heuristics = []

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

        print(self.__heuristics)

    # def __recalculateUB(self, upper_bound):
    #     if self.__upper_bound < upper_bound:
    #         self.__upper_bound = upper_bound
    #
    #     return self.__upper_bound

    def __apply_heuristics(self, heuristics):
        result = [heuristic(self.__problem.graph()) for heuristic in heuristics]
        print(result)

        self.__max_clique = max(result, key=len)
        self.__max_clique_len = len(self.__max_clique)

        return self.__max_clique, self.__max_clique_len

    def solve(self):
        self.__apply_heuristics(self.__heuristics)

        return self.__max_clique_len
