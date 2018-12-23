from cplex import Cplex
from networkx import Graph
from typing import List
from utils import get_independent_sets, problem_type, Objective, OBJECTIVE_SENSE, LinearConstraint, SENSE


def build_variables(vertices_number: int):
    return ['x' + str(x + 1) for x in range(0, vertices_number)]


def build_indepndent_set_constraint(independent_set: List[int], variables: List[str]):
    constraint_variables = [variables[node - 1] for node in independent_set]
    return LinearConstraint(constraint_variables, [1.0] * len(constraint_variables), SENSE.LOWER, 1.0)


def get_independent_set_constraints(independent_sets: List[List[int]], variables: List[str]):
    return [build_indepndent_set_constraint(independent_set, variables)
            for independent_set in independent_sets]


def build_edge_constraints(graph: Graph, variables: List[str]):
    constraints = []
    vertices_num = len(graph.nodes)

    for i in range(0, vertices_num):
        for j in range(i, vertices_num):
            if i != j and not graph.has_edge(i + 1, j + 1):
                constraint = LinearConstraint([variables[i], variables[j]], [1.0, 1.0], SENSE.LOWER, 1.0)
                # self.__log('Constraint: ', constraint)
                constraints.append(constraint)

    return constraints


def build_independent_set_problem(graph: Graph, dual_values: List[float]) -> Cplex:
    cplex = Cplex()

    vertices_number = len(graph.nodes)
    opt_point = dual_values[0:vertices_number]

    independent_sets = get_independent_sets(graph)
    variables = build_variables(vertices_number)
    objective = Objective(variables, OBJECTIVE_SENSE.MAX, type=problem_type.LP, var_type=cplex.variables.type.binary,
                          coefficients=opt_point)

    edge_constraints = build_edge_constraints(graph, variables)
    independent_sets_constraints = get_independent_set_constraints(independent_sets, variables)
    objective.set_to(cplex)
    LinearConstraint.set_many(cplex, edge_constraints)
    LinearConstraint.set_many(cplex, independent_sets_constraints)

    return cplex
