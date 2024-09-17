import graphviz
from .goal_tree import Goal, GoalTree

def draw_node(node: Goal, graph: graphviz.Digraph) -> None:
    '''Draw the current node and the links to its children
    in the given Digraph object.'''

    if node.is_pruned():
        graph.node(node.head, style='dotted')
    elif node.is_root():
        graph.node(node.head, color='gold', penwidth='2')
    else:  # normal
        graph.node(node.head)

    # green / red based on truth
    if node.truth == True:
        graph.node(node.head, style='filled', fillcolor='palegreen2')
    elif node.truth == False:
        graph.node(node.head, style='filled', fillcolor='lightpink1')
        
    for i, and_set in enumerate(node.body):
        if len(and_set) == 1:
            child = and_set[0]
            draw_node(child, graph)
            graph.edge(node.head, child.head)
        else:
            and_node_label = f'AND_{i}_{node.head}'
            graph.node(and_node_label, shape="point", width=".1", height='.1')
            graph.edge(node.head, and_node_label, arrowhead="none")
            for child in and_set:
                graph.edge(and_node_label, child.head)

                
def draw_tree(tree: GoalTree, graph: graphviz.Digraph) -> None:
    for node in tree.node_map.values():
        draw_node(node, graph)


def render_goal_tree(tree: GoalTree, dir="out", fn="diagram"):
    graph = graphviz.Digraph(strict=True)
    graph.attr(rankdir='RL')
    draw_tree(tree, graph)
    print('Drawing in ', dir, fn)
    graph.render(directory=dir,
                 filename=fn,
                 format="png")
