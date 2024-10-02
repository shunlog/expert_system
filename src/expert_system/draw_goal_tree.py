import graphviz

from .goal_tree import GoalTreeNode, FactNode, AndNode
from .DAG import DAG


def draw_node(graph: graphviz.Digraph, dag: DAG, node: GoalTreeNode):
    '''Draw the current node and the links to its children
    in the given Digraph object.'''

    head: str
    if isinstance(node, FactNode):
        head = node.fact
    else:
        assert isinstance(node, AndNode)
        head = node.parent_fact + str(node.id)

    if isinstance(node, AndNode):
        graph.node(head, label="", xlabel="AND", shape="circle", width="0.3")

    if node.pruned:
        graph.node(head, style='dotted')
    elif node in dag.all_starts():
        graph.node(head, color='gold', penwidth='2')
    else:  # normal
        graph.node(head)

    # green / red based on truth
    if node.truth == True:
        graph.node(head, style='filled', fillcolor='palegreen2')
    elif node.truth == False:
        graph.node(head, style='filled', fillcolor='lightpink1')

    for child_node in dag.successors(node):
        child_head = draw_node(graph, dag, child_node)
        graph.edge(head, child_head)

    return head


def draw_DAG(dag: DAG, graph: graphviz.Digraph) -> None:
    for node in dag.all_starts():
        draw_node(graph, dag, node)


def render_DAG(dag: DAG, dir="out", fn="diagram", format="png") -> str:
    graph = graphviz.Digraph(strict=True)
    graph.attr(rankdir='RL')

    draw_DAG(dag, graph)

    path = graph.render(directory=dir,
                        filename=fn,
                        format=format)
    return path
