import sys
from os import path, curdir, scandir


def Common_nodes(l1, l2):
    intersection = []
    for i in l1:
        if i in l2:
            intersection.append(i)
    return (intersection)


def clique_heur(G, nodes):
    d = nodes[0]
    spisok_vershin = []
    clique = []
    kandidates = nodes
    clique.append(kandidates[d])
    # print(kandidates)
    spisok_vershin = list(G.neighbors(kandidates[d]))
    # print('vershina ', kandidates[d], list(G.neighbors(kandidates[d])))
    kandidates.pop(d)
    # print (kandidates)

    while len(spisok_vershin) != 0:
        # print(spisok_vershin)

        for i in range(len(kandidates)):
            if spisok_vershin.count(kandidates[i]) != 0:
                break
        # print('vershina ', kandidates[i], list(G.neighbors(kandidates[i])))
        # print(kandidates[i])
        spisok_vershin = Common_nodes(spisok_vershin, list(G.neighbors(kandidates[i])))
        # print(spisok_vershin)
        clique.append(kandidates[i])
        kandidates.pop(i)
    # print (clique)
    return clique


if __name__ == '__main__':
    modules_dir = path.join(curdir, '..', 'modules')
    sys.path.append(modules_dir)

    from dimacs import DIMACS
    from max_clique import MaxCliqueSolver

    clq_dir = path.join(curdir, '../clq')
    # problem_path = path.join(clq_dir, 'c-fat200-2.clq')
    # problem = DIMACS(problem_path)

    # print(problem.description())

    files = scandir(clq_dir)

    for file in files:
        problem_path = path.join(clq_dir, file)
        problem = DIMACS(problem_path)
        print(problem.description())
        solver = MaxCliqueSolver(problem, [clique_heur])
        print(file, solver.solve(silent=True))
