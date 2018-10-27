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
    spisok_vershin = list(G.neighbors(kandidates[d]))
    kandidates.pop(d)

    while len(spisok_vershin) != 0:

        for i in range(len(kandidates)):
            if spisok_vershin.count(kandidates[i]) != 0:
                break
        spisok_vershin = Common_nodes(spisok_vershin, list(G.neighbors(kandidates[i])))
        clique.append(kandidates[i])
        kandidates.pop(i)
    return clique


if __name__ == '__main__':
    modules_dir = path.join(curdir, '..', 'modules')
    sys.path.append(modules_dir)

    from dimacs import DIMACS
    from max_clique import MaxCliqueSolver

    clq_dir = path.join(curdir, '../clq')

    files = scandir(clq_dir)

    for file in files:
        problem_path = path.join(clq_dir, file)
        problem = DIMACS(problem_path)
        print(problem.description())
        solver = MaxCliqueSolver(problem, [clique_heur])
        clique, size, duration = solver.solve(silent=True)
        print(file)
        print('''
            *** Maximum Clique Size {0}
            *** Maximum clique {1}
            *** Duration {2} ms
        '''.format(size, clique, duration))
        print('_' * 100)
