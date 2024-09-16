import graphviz
from goal_tree import Goal, GoalTree

def draw_node(node: Goal, graph: graphviz.Digraph) -> None:
    '''Recursively draw the current node,
    its children, and the links to them
    in the given Digraph object.'''
    if not node.is_leaf() and not node.is_root():
        graph.node(node.head, style='filled', color='lightgrey')
    elif node.is_root():
        graph.node(node.head, style='filled', color='palegreen2')
    else:
        graph.node(node.head)
        
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
                draw_node(child, graph)
                graph.edge(and_node_label, child.head)

                
def draw_tree(tree: GoalTree, graph: graphviz.Digraph) -> None:
    for root in tree.roots:
        draw_node(root, graph)


def render_goal_tree(tree: GoalTree):
    graph = graphviz.Digraph(strict=True)
    graph.attr(rankdir='RL')
    draw_tree(tree, graph)
    graph.render(directory="graphviz-output", format="png")
