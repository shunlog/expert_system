'''paradag
https://github.com/xianghuzhao/paradag
MIT license.
'''


class _dagData(object):
    '''The internal data of DAG'''

    def __init__(self):
        self.__graph = {}
        self.__graph_reverse = {}

    def vertices(self):
        '''Get the vertices list'''
        return set(self.__graph.keys())

    def add_vertex(self, vertex):
        '''Add a new vertex'''
        if vertex not in self.__graph:
            self.__graph[vertex] = set()
            self.__graph_reverse[vertex] = set()

    def add_edge(self, v_from, v_to):
        '''Add an edge from one vertex to another'''
        self.__graph[v_from].add(v_to)
        self.__graph_reverse[v_to].add(v_from)

    def remove_edge(self, v_from, v_to):
        '''Remove an edge from one vertex to another'''
        self.__graph[v_from].remove(v_to)
        self.__graph_reverse[v_to].remove(v_from)

    def successors(self, vertex):
        '''Get the successors of the specified vertex'''
        return self.__graph[vertex]

    def predecessors(self, vertex):
        '''Get the predecessors of the specified vertex'''
        return self.__graph_reverse[vertex]


class DAG(object):
    '''DAG '''

    def __init__(self):
        self.__data = _dagData()

    def __validate_vertex(self, *vertices):
        for vtx in vertices:
            if vtx not in self.__data.vertices():
                raise ValueError(
                    'Vertex "{0}" does not belong to DAG'.format(vtx))

    def __has_path_to(self, v_from, v_to):
        if v_from == v_to:
            return True
        for vtx in self.__data.successors(v_from):
            if self.__has_path_to(vtx, v_to):
                return True
        return False

    def vertices(self):
        '''Get the vertices list'''
        return self.__data.vertices()

    def __eq__(self, other):
        if not isinstance(other, DAG):
            return False

        def equal_vertex_sets(self_vset, other_vset):
            # check that the two vertex sets have the same values,
            # which is possible since the values must be hashable
            if self_vset != other_vset:
                return False
            # recursively check that all the children are the same
            # for the nodes with the same value in each set
            for v in self_vset:
                self_succ = self.successors(v)
                other_succ = other.successors(v)
                if not equal_vertex_sets(self_succ, other_succ):
                    return False
            return True

        return equal_vertex_sets(self.all_starts(), other.all_starts())

    def add_vertex(self, *vertices):
        '''Add one or more vertices'''
        for vtx in vertices:
            self.__data.add_vertex(vtx)

    def add_edge(self, v_from, *v_tos):
        '''Add edge(s) from one vertex to others'''
        self.__validate_vertex(v_from, *v_tos)

        for v_to in v_tos:
            if self.__has_path_to(v_to, v_from):        # pylint: disable=arguments-out-of-order
                raise ValueError(
                    'Cycle if add edge from "{0}" to "{1}"'.format(v_from, v_to))
            self.__data.add_edge(v_from, v_to)

    def remove_edge(self, v_from, v_to):
        '''Remove an edge from one vertex to another'''
        self.__validate_vertex(v_from, v_to)
        if v_to not in self.__data.successors(v_from):
            raise ValueError(
                'Edge not found from "{0}" to "{1}"'.format(v_from, v_to))

        self.__data.remove_edge(v_from, v_to)

    def vertex_size(self):
        '''Get the number of vertices'''
        return len(self.__data.vertices())

    def edge_size(self):
        '''Get the number of edges'''
        size = 0
        for vtx in self.__data.vertices():
            size += self.outdegree(vtx)
        return size

    def successors(self, vertex):
        '''Get the successors of the specified vertex'''
        self.__validate_vertex(vertex)
        return self.__data.successors(vertex)

    def predecessors(self, vertex):
        '''Get the predecessors of the specified vertex'''
        self.__validate_vertex(vertex)
        return self.__data.predecessors(vertex)

    def indegree(self, vertex):
        '''Get the indegree of the specified vertex'''
        return len(self.predecessors(vertex))

    def outdegree(self, vertex):
        '''Get the outdegree of the specified vertex'''
        return len(self.successors(vertex))

    def __endpoints(self, degree_callback):
        endpoints = set()
        for vtx in self.__data.vertices():
            if degree_callback(vtx) == 0:
                endpoints.add(vtx)
        return endpoints

    def all_starts(self):
        '''Get all the starting vertices'''
        return self.__endpoints(self.indegree)

    def all_terminals(self):
        '''Get all the terminating vertices'''
        return self.__endpoints(self.outdegree)


def test_equality():

    def big_dag():
        dag = DAG()
        dag.add_vertex("feathers")
        dag.add_vertex("flies")
        dag.add_vertex("bird")
        dag.add_vertex(0)
        dag.add_vertex(1)
        dag.add_edge(0, "feathers")
        dag.add_edge(1, "flies")

        dag.add_vertex("penguin")
        dag.add_vertex(2)
        dag.add_vertex("swims")
        dag.add_edge(2, "swims")
        dag.add_edge(2, "bird")

        dag.add_vertex("albatross")
        dag.add_vertex(3)
        dag.add_vertex("good flyer")
        dag.add_edge(3, "bird")
        dag.add_edge(3, "good flyer")
        return dag

    dag1 = big_dag()
    dag2 = big_dag()

    assert dag1 == dag2
    dag2.remove_edge(3, "bird")
    assert dag1 != dag2

    dag3 = big_dag()
    dag3.add_vertex("extra")
    assert dag1 != dag3
