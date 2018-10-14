from networkx import Graph


class DIMACS:
    __graph = None
    __description = ''
    __vertices_num = 0
    __edges_num = 0

    def graph(self):
        return self.__graph

    def description(self):
        return self.__description

    def vertices_num(self):
        return self.__vertices_num

    def edges_num(self):
        return self.__edges_num

    def __init__(self, filepath):
        self.__parse(filepath)

    def __parse(self, filepath):
        file = open(filepath, 'r')
        edges = []

        for line in file:
            line_type, content = self.__unpack_line(line)

            if line_type == 'c':
                self.__description += content
                continue

            if line_type == 'p':
                (self.__vertices_num, self.__edges_num) = content.split()[1:]
                continue

            if line_type == 'e':
                edge = content.split(' ', 1)
                edges.append(edge)

        self.__graph = Graph(edges)

    def __unpack_line(self, line):
        try:
            line_type, content = line.split(' ', 1)

            return line_type, content
        except:
            return line, '\n'
