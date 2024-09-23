#!/bin/env python3
from icecream import ic
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache

from .DAG import DAG
from .three_valued_logic import and3, or3

# A GoalTree is represented by a dict:
# the keys are strings representing nodes which in turn represent facts
# the values are sets of tuples, representing


@dataclass(frozen=True)
class GoalTreeNode:
    truth: Optional[bool] = field(default=None, kw_only=True)
    pruned: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class AndNode(GoalTreeNode):
    parent_fact: str  # the fact string of its parent
    id: int  # the order in which it appears in the rule definition


@dataclass(frozen=True)
class FactNode(GoalTreeNode):
    fact: str


def construct_dag(rules):
    dag = DAG()
    # 1. add all vertices
    for fact, and_sets in rules.items():
        dag.add_vertex(FactNode(fact))
        for and_set in and_sets:
            for child_fact in and_set:
                dag.add_vertex(FactNode(child_fact))

    # 2. add all AND-nodes and all edges
    for fact, and_sets in rules.items():
        for i, and_set in enumerate(and_sets):
            assert len(and_set) >= 1
            node = FactNode(fact)
            if len(and_set) == 1:
                child_fact = next(and_set.__iter__())
                dag.add_edge(node, FactNode(child_fact))
            else:
                and_node = AndNode(fact, i)
                dag.add_vertex(and_node)
                dag.add_edge(node, and_node)
                for child_fact in and_set:
                    dag.add_edge(and_node, FactNode(child_fact))
    return dag


def update_truth(dag: DAG, assertions: dict[str, bool]) -> DAG:
    '''Using top-down recursion, recreate the DAG
    while evaluating each node's truth based on the given assertions,
    which match facts to their truth values.'''
    new_dag = DAG()

    # a FactNode can have multiple parents which will call add_node on it,
    # but the add_node function is idempotent, so we can cache it
    @lru_cache(maxsize=None)
    def add_node(node: GoalTreeNode) -> GoalTreeNode:
        '''For a node in the old dag compute all the children recursively,
        then compute the new node and add it to the new dag
        together with the links to its new children'''
        new_node: GoalTreeNode

        # base case: leaf node
        if dag.outdegree(node) == 0:
            assert isinstance(node, FactNode)
            fact = node.fact
            truth = assertions.get(fact)
            new_node = FactNode(fact, truth=truth)
            new_dag.add_vertex(new_node)
            return new_node

        # recursive case
        new_children = [add_node(succ) for succ in dag.successors(node)]
        children_truths = [n.truth for n in new_children]
        if isinstance(node, FactNode):
            # check the assertions even for intermediary nodes
            # to allow for groups of mutually exclusive facts
            if (truth := assertions.get(node.fact)) is None:
                truth = or3(children_truths)
            new_node = FactNode(node.fact, truth=truth)
        else:
            assert isinstance(node, AndNode)
            truth = and3(children_truths)
            new_node = AndNode(node.parent_fact, node.id, truth=truth)

        new_dag.add_vertex(new_node)
        for new_child in new_children:
            new_dag.add_edge(new_node, new_child)

        return new_node

    for root in dag.all_starts():
        add_node(root)

    return new_dag


rules = ({"penguin": ({"bird", "swims"},),
          "bird": ({"feathers"}, {"flies"}),
          "albatross": ({"bird", "good flyer"},)})


def test_construct_dag():
    dag = DAG()
    fn_feathers = FactNode("feathers")
    fn_flies = FactNode("flies")
    fn_bird = FactNode("bird")
    fn_penguin = FactNode("penguin")
    an_penguin_0 = AndNode("penguin", 0)
    fn_swims = FactNode("swims")
    fn_albatross = FactNode("albatross")
    an_albatross_0 = AndNode("albatross", 0)
    fn_good_flyer = FactNode("good flyer")

    dag.add_vertex(fn_feathers, fn_flies, fn_bird, fn_penguin,
                   an_penguin_0, fn_swims, fn_albatross, an_albatross_0,
                   fn_good_flyer)

    dag.add_edge(fn_penguin, an_penguin_0)
    dag.add_edge(an_penguin_0, fn_swims, fn_bird)
    dag.add_edge(fn_bird, fn_feathers)
    dag.add_edge(fn_bird, fn_flies)
    dag.add_edge(fn_albatross, an_albatross_0)
    dag.add_edge(an_albatross_0, fn_bird, fn_good_flyer)

    dag2 = construct_dag(rules)

    assert dag == dag2


def test_update_dag_truth_1():
    assertions = {"flies": True}

    dag = DAG()
    # OR node
    fn_flies = FactNode("flies", truth=True)
    fn_bird = FactNode("bird", truth=True)

    fn_feathers = FactNode("feathers")
    fn_penguin = FactNode("penguin")
    an_penguin_0 = AndNode("penguin", 0)
    fn_swims = FactNode("swims")
    fn_albatross = FactNode("albatross")
    an_albatross_0 = AndNode("albatross", 0)
    fn_good_flyer = FactNode("good flyer")

    dag.add_vertex(fn_feathers, fn_flies, fn_bird, fn_penguin,
                   an_penguin_0, fn_swims, fn_albatross, an_albatross_0,
                   fn_good_flyer)

    dag.add_edge(fn_penguin, an_penguin_0)
    dag.add_edge(an_penguin_0, fn_swims, fn_bird)
    dag.add_edge(fn_bird, fn_feathers)
    dag.add_edge(fn_bird, fn_flies)
    dag.add_edge(fn_albatross, an_albatross_0)
    dag.add_edge(an_albatross_0, fn_bird, fn_good_flyer)

    dag2 = update_truth(construct_dag(rules), assertions)
    assert dag == dag2


def test_update_dag_truth_2():
    assertions = {"flies": True,
                  "swims": True}

    dag = DAG()

    fn_flies = FactNode("flies", truth=True)
    fn_swims = FactNode("swims", truth=True)
    # OR + AND node
    fn_bird = FactNode("bird", truth=True)
    an_penguin_0 = AndNode("penguin", 0, truth=True)
    fn_penguin = FactNode("penguin", truth=True)

    # unchanged
    fn_feathers = FactNode("feathers")
    fn_albatross = FactNode("albatross")
    an_albatross_0 = AndNode("albatross", 0)
    fn_good_flyer = FactNode("good flyer")

    dag.add_vertex(fn_feathers, fn_flies, fn_bird, fn_penguin,
                   an_penguin_0, fn_swims, fn_albatross, an_albatross_0,
                   fn_good_flyer)

    dag.add_edge(fn_penguin, an_penguin_0)
    dag.add_edge(an_penguin_0, fn_swims, fn_bird)
    dag.add_edge(fn_bird, fn_feathers)
    dag.add_edge(fn_bird, fn_flies)
    dag.add_edge(fn_albatross, an_albatross_0)
    dag.add_edge(an_albatross_0, fn_bird, fn_good_flyer)

    dag2 = update_truth(construct_dag(rules), assertions)
    assert dag == dag2


def test_update_truth_unchanged():
    dag = DAG()
    fn_feathers = FactNode("feathers")
    fn_flies = FactNode("flies")
    fn_bird = FactNode("bird")
    fn_penguin = FactNode("penguin")
    an_penguin_0 = AndNode("penguin", 0)
    fn_swims = FactNode("swims")
    fn_albatross = FactNode("albatross")
    an_albatross_0 = AndNode("albatross", 0)
    fn_good_flyer = FactNode("good flyer")

    dag.add_vertex(fn_feathers, fn_flies, fn_bird, fn_penguin,
                   an_penguin_0, fn_swims, fn_albatross, an_albatross_0,
                   fn_good_flyer)

    dag.add_edge(fn_penguin, an_penguin_0)
    dag.add_edge(an_penguin_0, fn_swims, fn_bird)
    dag.add_edge(fn_bird, fn_feathers)
    dag.add_edge(fn_bird, fn_flies)
    dag.add_edge(fn_albatross, an_albatross_0)
    dag.add_edge(an_albatross_0, fn_bird, fn_good_flyer)

    dag2 = update_truth(construct_dag(rules), {})
    assert dag == dag2


def test_update_truth_intermediate_node():
    # set intermediate node "bird" to True
    # and check that its child "flies" is still set to False
    assertions = {"bird": True,
                  "flies": False}
    dag = DAG()
    fn_flies = FactNode("flies", truth=False)
    fn_bird = FactNode("bird", truth=True)

    fn_feathers = FactNode("feathers")
    fn_penguin = FactNode("penguin")
    an_penguin_0 = AndNode("penguin", 0)
    fn_swims = FactNode("swims")
    fn_albatross = FactNode("albatross")
    an_albatross_0 = AndNode("albatross", 0)
    fn_good_flyer = FactNode("good flyer")

    dag.add_vertex(fn_feathers, fn_flies, fn_bird, fn_penguin,
                   an_penguin_0, fn_swims, fn_albatross, an_albatross_0,
                   fn_good_flyer)

    dag.add_edge(fn_penguin, an_penguin_0)
    dag.add_edge(an_penguin_0, fn_swims, fn_bird)
    dag.add_edge(fn_bird, fn_feathers)
    dag.add_edge(fn_bird, fn_flies)
    dag.add_edge(fn_albatross, an_albatross_0)
    dag.add_edge(an_albatross_0, fn_bird, fn_good_flyer)

    dag2 = update_truth(construct_dag(rules), assertions)
    assert dag == dag2


if __name__ == "__main__":
    test_update_dag_truth_1()
    test_update_truth_unchanged()
