import sys
from os import path, curdir, scandir
from re import match, compile


if __name__ == '__main__':
    modules_dir = path.join(curdir, '..', 'modules')
    sys.path.append(modules_dir)

    from dimacs import DIMACS
    from branch_and_price import BranchAndPriceSolver
    from utils import Timer

    regexp = compile("^.*\.col$")

    clq_dir = path.join(curdir, '../coloring')

    files = list(filter(lambda file: regexp.match(file.name), scandir(clq_dir)))

    for file in files:
        problem_path = path.join(clq_dir, file.name)
        problem = DIMACS(problem_path)
        print(problem.description())
        solver = BranchAndPriceSolver(problem)

        timer = Timer()
        timer.start()
        colors, coloring = solver.solve(silent=True)
        timer.stop()
        print(file)
        print('''
            *** Min colors {0}
            *** Min coloring {1}
            *** Duration {2} ms
        '''.format(colors, coloring, timer.duration()))
        print('_' * 100)
