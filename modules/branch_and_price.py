from dimacs import DIMACS
from cplex import Cplex
from utils import get_independent_sets, problem_type, build_variables, Objective, OBJECTIVE_SENSE, \
    LinearConstraint, SENSE, is_integer, is_one, get_maximal_independent_set, compare, nonint_items
from networkx import Graph
from typing import List
from math import inf, floor
import sys
from isp_utils import build_independent_set_problem


class BranchAndPriceSolver:
    _variable_prefix = 'x'
    _min_colors = inf
    _min_coloring = None
    _independent_sets = []

    def __init__(self, problem: DIMACS, limit=2):
        self._problem: DIMACS = problem
        self._graph: Graph = problem.graph()
        self._limit = limit

        self._init_cplex()

    def _build_vars(self, independent_sets: List[List[int]]):
        return build_variables(independent_sets, prefix=self._variable_prefix)

    def _build_constraints(self, nodes: List[int], independent_sets: List[List[int]]):
        constraints = []
        for node in nodes:
            variables = []
            for i in range(0, len(independent_sets)):
                independent_set = independent_sets[i]
                if node in independent_set:
                    variables.append(self._variable_prefix + str(i + 1))
            constraint = LinearConstraint(variables, [1.0] * len(variables), SENSE.GREATER, 1.0)
            constraints.append(constraint)

        return constraints

    def _init_cplex(self):
        self.cplex = Cplex()

        independent_sets = get_independent_sets(self._graph)
        variables = self._build_vars(independent_sets)
        objective = Objective(variables, OBJECTIVE_SENSE.MIN, type=problem_type.LP, lb=0.0)

        # self.__log('Variables: ', variables)

        constraints = self._build_constraints(list(self._graph.nodes), independent_sets)
        # self.__log('Constraints count: ', len(constraints))
        objective.set_to(self.cplex)
        LinearConstraint.set_many(self.cplex, constraints)
        self._independent_sets = independent_sets

    def _make_silence(self, cplex: Cplex):
        cplex.set_log_stream(None)
        cplex.set_warning_stream(None)
        cplex.set_error_stream(None)
        cplex.set_results_stream(None)

    def _has_broken_constraint(self, dual_value):
        for value in dual_value:
            if compare(value, 1.0) == -1:
                return True
        return False

    def _validate_coloring(self, opt_point):
        for index in range(0, len(opt_point)):
            if not is_integer(opt_point[index]):
                return False

        return True

    def _get_coloring(self, opt_point):
        return [index + 1 for index in range(0, len(opt_point)) if is_one(opt_point[index])]

    def _add_independent_set(self, independent_set):
        variable = self._variable_prefix + str(self.cplex.variables.get_num() + 1)
        for node in independent_set:
            self.cplex.variables.add(names=[variable], lb=[0.0], obj=[1.0])
            self.cplex.linear_constraints.set_linear_components(LinearConstraint.get_node_constraint_name(node=node),
                                                                [[variable], [1.0]])

    def solve_strict_max_independent_set_problem(self, dual_values):
        problem = build_independent_set_problem(self._graph, dual_values)

        if self.silent:
            self._make_silence(problem)

        try:
            problem.solve()
        except:
            return

        solution = problem.solution.get_objective_value()
        opt_point = problem.solution.get_values()

        if compare(solution, 1.0) != 1:
            return

        return [index + 1 for index, value in enumerate(opt_point) if opt_point[index] == 1.0], solution

    def _try_add_stronger_constraints(self, dual_values, solution):
        count = 0

        while count < self._limit:
            values = dual_values[0:len(self._graph.nodes)]
            if not self._has_broken_constraint(values):
                return

            max_independent_set_result = get_maximal_independent_set(self._graph, values)

            if max_independent_set_result:
                max_independent_set, max_independent_set_value = max_independent_set_result

            else:
                strict_solution = self.solve_strict_max_independent_set_problem(dual_values)

                if not strict_solution:
                    return False

                max_independent_set, max_independent_set_value = strict_solution

            if compare(max_independent_set_value, 1.0) != 1:
                strict_solution = self.solve_strict_max_independent_set_problem(dual_values)

                if strict_solution:
                    max_independent_set, max_independent_set_value = strict_solution

            if compare(max_independent_set_value, 1.0) != 1:
                return False

            self._add_independent_set(max_independent_set)
            try:
                self.cplex.solve()
            except:
                return False

            new_solution = self.cplex.solution.get_objective_value()

            if compare(solution, new_solution) == 0:
                count += 1
            else:
                count = 0

            dual_values = self.cplex.solution.get_dual_values()

        return True

    def _get_branching_variable(self, variables, opt_point):
        """

        :type nodes: list
        """
        for index in range(0, len(variables)):
            variable = variables[index]
            value = opt_point[index]
            if not is_integer(value):
                return variable, index, value

    def _get_min_colors(self, solution):
        return solution if is_integer(solution) else floor(solution) + 1

    def _branching(self):
        try:
            self.cplex.solve()
        except:
            return

        solution = self.cplex.solution.get_objective_value()
        opt_point = self.cplex.solution.get_values()
        min_colors = self._get_min_colors(solution)
        # print(self._min_colors, solution, min_colors, opt_point)

        if compare(solution, self._min_colors) == 1:
            return

        if self._validate_coloring(opt_point) and min_colors < self._min_colors:
            self._min_colors = min_colors
            self._min_coloring = self._get_coloring(opt_point)


        dual_values = self.cplex.solution.get_dual_values()
        if not self._try_add_stronger_constraints(dual_values, solution):
            return

        # нужно получить новое решение, после добавления новых ограничений, тк там возможно получение нового решения
        solution = self.cplex.solution.get_objective_value()
        opt_point = self.cplex.solution.get_values()
        min_colors = self._get_min_colors(solution)
        # print(self._min_colors, solution, min_colors, opt_point)

        branch = self._get_branching_variable(self.cplex.variables.get_names(), opt_point)
        print(branch)

        if not branch:
            if self._validate_coloring(opt_point) and min_colors < self._min_colors:
                self._min_colors = min_colors
                self._min_coloring = self._get_coloring(opt_point)

            # self._branching()
            return


        branch_variable, branch_index, branch_value = branch
        self.cplex.linear_constraints.add(names=[str(branch_variable)],
                                          lin_expr=[[[branch_variable], [1.0]]],
                                          senses=[SENSE.LOWER.value],
                                          rhs=[0.0])

        self._branching()

        self.cplex.linear_constraints.delete(str(branch_variable))

        self.cplex.linear_constraints.add(names=[branch_variable],
                                          lin_expr=[[[branch_variable], [1.0]]],
                                          senses=[SENSE.GREATER.value],
                                          rhs=[1.0])
        self._branching()
        self.cplex.linear_constraints.delete(str(branch_variable))

    def solve(self, silent=False):
        self.silent = silent

        if self.silent:
            self._make_silence(self.cplex)

        try:
            self._branching()
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print("Unexpected error:", sys.exc_info()[0])

        return self._min_colors, self._min_coloring
