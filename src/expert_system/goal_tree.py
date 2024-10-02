#!/bin/env python3
from icecream import ic
from dataclasses import dataclass, field, replace
from typing import Optional
from functools import cache
from frozendict import frozendict
from math import sqrt
import pytest
from collections import OrderedDict

from .DAG import DAG
from .three_valued_logic import and3, or3

'''
This program implements an Expert system that asks the user yes/no questions
to help them identify a type of person, similar to Akinator.
An expert system is divided into two subsystems:
1) a knowledge base, which represents facts and rules; and
2) an inference engine, which applies the rules to the known facts to deduce new facts.

A goal tree is a graphical representation of a set of rules for solving a problem.
A goal tree can only represent rules of this form:
  - X if A1 and A2 and ...
There can be multiple rules for the same X which are treated as alternatives.
Thus we can also write a generalized rule structure like this ("..." means zero or more):
  - X if OR(AND(goal, ...), ...)

To implement the expert system, we'll be using an augmented representation of a goal tree,
which will act both as the knowledge base, as well as the inference engine.
A goal tree can be represented with a Directed Acyclic Graph (DAG).
Each node can have a truth value: either True, False or Unknown (represented by None).

There are two kinds of rule-based systems:
    - Production systems, which use if-then rules to derive actions from conditions.
    - Logic programming systems, which use conclusion if conditions rules to derive
      conclusions from conditions.
As opposed to production systems where we only need to provide data as a list of facts that are true,
in an expert system we need to be able to represent that a statement is false
for the optimization of asking questions and deducing facts.
'''


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


def geometric_mean(a, b):
    return sqrt(a * b)


def construct_dag(rules: dict[str, tuple[set[str], ...]]):
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


def update_truth(dag: DAG, assertions: frozendict[str, Optional[bool]]) -> DAG:
    '''Using top-down recursion, recreate the DAG
    while evaluating each node's truth based on the given assertions,
    which match facts to their truth values.'''
    new_dag = DAG()

    # a FactNode can have multiple parents which will call add_node on it,
    # but the add_node function is idempotent, so we can cache it
    @cache
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


def update_truth_with_groups(
        dag: DAG, assertions: frozendict[str, Optional[bool]],
        exclusive_groups: tuple[set[str], ...] = tuple()):
    '''A wrapper around the update_truth() function
    which takes exclusive groups into account.

    Works by repeatedly:
    1) inferring new assertions using from the original assertions
    and the list of exclusive_groups,
    2) applying update_truth()
    until the second step can't infer any new facts.
    '''
    while True:
        new_dag = update_truth(dag, assertions)
        truths = dag_truths(new_dag)
        excluded_facts: list[str] = []
        for group in exclusive_groups:
            true_facts = [fact for fact in group if truths.get(fact) == True]
            if not true_facts:
                continue
            if len(true_facts) > 1:
                raise ValueError(
                    "Only one fact from each exclusive group can be true.")
            match = true_facts[0]
            excluded_facts.extend(group - {match})
        if not excluded_facts:
            break
        old_truths = truths
        truths = truths | {f: False for f in excluded_facts}
        if old_truths == truths:
            break
        assertions = frozendict(truths)
    return new_dag


def update_pruned(dag: DAG) -> DAG:
    '''
    Using bottom-up recursion, recreate the DAG
    but with the pruned state of each node re-evaluated.

    A node is "pruned" when we don't care to find out its truth value.
    This is useful for minimizing the number of questions asked.

    A node is pruned if each of its parents either:
    1. has a known truth (not None)
    2. is pruned
    '''
    # TODO add that node is pruned if it's contained in all the and-sets of the remaining roots
    # need the entire Tree for that, to check if there are any other remaining roots
    new_dag = DAG()

    # the add_node function is idempotent, so we can cache it
    @cache
    def add_node(node: GoalTreeNode) -> GoalTreeNode:
        '''For a node in the old dag, compute all the parents recursively,
        then compute the new node and add it to the new dag
        together with the links from its parents.'''
        new_node: GoalTreeNode
        # base case: root node
        if dag.indegree(node) == 0:
            new_dag.add_vertex(node)
            # assuming root nodes can't be pruned
            return node
        # recursive case
        new_parents = [add_node(p) for p in dag.predecessors(node)]
        pruned = node.truth is None and all(
            ((p.truth is not None) or p.pruned) for p in new_parents)
        new_node = replace(node, pruned=pruned)
        new_dag.add_vertex(new_node)
        for new_parent in new_parents:
            new_dag.add_edge(new_parent, new_node)
        return new_node

    for leaf in dag.all_terminals():
        add_node(leaf)

    return new_dag


def solution(dag: DAG) -> Optional[str]:
    '''Returns None if solution is not yet known.
    Returns the fact string if it is the only solution.
    Otherwise, raises an error if there are multiple true roots,
    or if all the roots are false.'''
    true = [n.fact for n in dag.all_starts() if n.truth == True]
    false = [n.fact for n in dag.all_starts() if n.truth == False]
    unknown = [n.fact for n in dag.all_starts() if n.truth == None]
    if len(true) == 1:
        return true[0]
    elif len(true) > 1:
        raise ValueError("More than one hypothesis are true.")
    elif len(false) == len(dag.all_starts()):
        raise ValueError("More than one hypothesis are true.")
    elif len(unknown) == 1:
        return unknown[0]
    return None


@dataclass(frozen=True)
class GoalTree:
    '''
    This is a helper class to keep the DAG together with the exclusive groups,
    and to automatically updated it when the assertions are changed.

    - dag: the DAG, evaluated using the assertions
    - rules: representation of the if-then rules,
        the mapping of facts to the and-sets
    - exclusive_groups: list of sets of facts,
        such that at most one element of each set can be true
    - assertions: mapping of facts to their truth value
    '''
    rules: dict[str, tuple[set[str], ...]]
    exclusive_groups: tuple[set[str], ...] = tuple()
    assertions: frozendict[str, bool] = frozendict()
    dag: DAG = None
    check_guaranteed: bool = False

    def __post_init__(self):
        if not isinstance(self.assertions, frozendict):
            object.__setattr__(self, "assertions", frozendict(self.assertions))

        dag = self.dag
        if not self.dag:
            # don't reconstruct skeleton when simply updating the assertions
            dag = construct_dag(self.rules)

        dag = update_pruned(
            update_truth_with_groups(dag, self.assertions, self.exclusive_groups))

        if self.check_guaranteed:
            guaranteed_assertions = update_guaranteed(dag,
                                                      self.assertions,
                                                      self.exclusive_groups)
            dag = update_pruned(
                update_truth_with_groups(dag, guaranteed_assertions, self.exclusive_groups))

        object.__setattr__(self, "dag", dag)

    def set(self, new_assertions: dict[str, bool]):
        return GoalTree(self.rules,
                        self.exclusive_groups,
                        self.assertions | new_assertions,
                        self.dag)


def node_value(gt: GoalTree, node: FactNode) -> dict:
    '''
    Computes the parameters that define the questioning value of a node.
    '''
    # goal tree if node is true
    gt_true = gt.set({node.fact: True})

    # goal tree if node is false
    gt_false = gt.set({node.fact: False})

    def roots_turned_false(new_gt):
        start = sum(1 for r in gt.dag.all_starts() if r.truth == False)
        end = sum(1 for r in new_gt.dag.all_starts() if r.truth == False)
        return end-start

    def leaves_pruned(new_gt):
        start = sum(1 for r in gt.dag.all_terminals() if r.pruned)
        end = sum(1 for r in new_gt.dag.all_terminals() if r.pruned)
        return end-start

    rf = roots_turned_false(gt_false)
    rt = roots_turned_false(gt_true)
    lf = leaves_pruned(gt_false)
    lt = leaves_pruned(gt_true)
    # a geometric mean is higher than a regular mean when the values are closer together.
    # we want questions that have a larger impact both when true and when false,
    # otherwise the more specific questions will get a higher value.
    # By adding 1 to each value, we ensure that the result is not 0 when either is 0
    # value = geometric_mean(rf+1, rt+1)
    value = 3 * geometric_mean(rf+1, rt+1) + 1 * geometric_mean(lf+1, lt+1)

    return {"value": value,
            "roots_cut_if_false": rf,
            "roots_cut_if_true": rt,
            "leaves_pruned_if_false": lf,
            "leaves_pruned_if_true": lt}


def update_guaranteed(
        dag: DAG, assertions: frozendict[str, Optional[bool]],
        exclusive_groups: tuple[set[str], ...] = tuple()
) -> frozendict[str, Optional[bool]]:
    '''Given a evaluated DAG, check if the truth of any leaves is guaranteed.
    Return the augmented dict of assertions.

    We make the assumption that one and only one root will be True,
    therefore in some cases we can guarantee that a leaf can only be true or false.'''

    updates: dict[str, bool] = {}
    for leaf in dag.all_terminals():
        # Ideally we would check all nodes, not just the leaves
        # but that's too slow with the current approach
        dag_false = update_truth_with_groups(
            dag, assertions.set(leaf.fact, False), exclusive_groups)
        must_be_false = False
        must_be_true = False

        try:
            # this line can fail because of exclusive groups (for some reason)
            dag_true = update_truth_with_groups(
                dag, assertions.set(leaf.fact, True), exclusive_groups)
            try:
                solution(dag_true)
            except ValueError:
                must_be_false = True
        except ValueError:
            pass
        try:
            solution(dag_false)
        except ValueError:
            must_be_true = True

        if must_be_false and must_be_true:
            raise ValueError(
                f'Leaf {leaf} can\'t be set to either true or false.')
        if must_be_true:
            updates |= {leaf.fact: True}
        if must_be_false:
            updates |= {leaf.fact: False}
    return assertions | updates


def dag_truths(dag: DAG) -> dict[str, Optional[bool]]:
    """Given a Goal Tree DAG, return a dict mapping the facts to their truth value."""
    return {n.fact: n.truth
            for n in dag.vertices() if isinstance(n, FactNode)}


def dag_backward_chain(dag: DAG, fact: str) -> OrderedDict[FactNode, None]:
    '''Returns ordered dict of intermediary fact nodes.'''
    children = OrderedDict()

    def backward_chain(node):
        if dag.outdegree(node) == 0:
            return
        if isinstance(node, FactNode):
            children[node] = None
        for child in dag.successors(node):
            backward_chain(child)

    node = next((n for n in dag.vertices() if isinstance(
        n, FactNode) and n.fact == fact))
    backward_chain(node)
    return children


def encyclopedia_of_fact(dag: DAG, fact: str):
    '''Returns an HTML string describing the fact.'''
    interm = dag_backward_chain(dag, fact)
    s = '<dl>'
    for node in interm.keys():
        s += f'<dt> {node.fact} </dt>\n<dd><ul>\n'
        for i, child in enumerate(dag.successors(node)):
            s += '<li>\n'
            if i != 0:
                s += 'OR, '
            if isinstance(child, AndNode):
                s += ' AND '.join(n.fact for n in dag.successors(child))
            else:
                s += f'{child.fact}'
            s += '</li>\n'
        s += '</ul></dd>\n'
    return s


rules = {"penguin": ({"bird", "swims"},),
         "bird": ({"feathers"}, {"flies"}),
         "albatross": ({"bird", "good flyer"},)}


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


def test_update_truth_assertion_over_inferred():
    rules = {"A": tuple({"B"}),
             "B": tuple({"C"})}
    assertions = {"B": False,
                  "C": True}
    dag = DAG()
    # even though C is true making B true,
    # B should stay False because that's an assertion
    a = FactNode("A", truth=False)
    b = FactNode("B", truth=False)
    c = FactNode("C", truth=True)
    dag.add_vertex(a, b, c)
    dag.add_edge(a, b)
    dag.add_edge(b, c)
    dag2 = update_truth(construct_dag(rules),
                        assertions)
    assert dag == dag2


def test_update_truth_with_exclusive_groups():
    rules = {"F": ({"A", "B", "C"}, {"D"}),
             "A": ({"S"},)}
    assertions = {"S": True}
    exclusive_groups = ({"A", "B", "C"},)
    gt = GoalTree(rules, exclusive_groups, assertions)
    dag = update_truth_with_groups(gt.dag, assertions, exclusive_groups)
    truths = dag_truths(dag)

    assert truths == {"S": True, "A": True,
                      "B": False, "C": False, "F": None, "D": None}


def test_update_pruned_AND():
    rules = {"A": ({"B", "C", "D"},
                   {"E"}),
             "E": tuple({"D"})}
    assertions = {"B": False}

    # B is false, therefore the and-node is false
    # therefore C is pruned
    # but D is not pruned because it still has an unknown parent
    a = FactNode("A")
    a_and = AndNode("A", 0, truth=False)
    b = FactNode("B", truth=False)
    c = FactNode("C", pruned=True)
    d = FactNode("D")
    e = FactNode("E")
    dag = DAG()
    dag.add_vertex(a, a_and, b, c, d, e)
    dag.add_edge(a, a_and)
    dag.add_edge(a_and, b, c, d)
    dag.add_edge(a, e)
    dag.add_edge(e, d)

    dag2 = update_pruned(update_truth(construct_dag(rules),
                                      assertions))
    assert dag == dag2


def test_update_pruned_OR():
    rules = {"A": ({"B"}, {"C"}, {"D"}),
             "E": ({"D"},)}
    assertions = {"B": True}

    # B is True, therefore A is True
    # therefore C is pruned
    # but D is not pruned because it still has an unknown parent
    a = FactNode("A", truth=True)
    b = FactNode("B", truth=True)
    c = FactNode("C", pruned=True)
    d = FactNode("D")
    e = FactNode("E")
    dag = DAG()
    dag.add_vertex(a, b, c, d, e)
    dag.add_edge(a, b, c, d)
    dag.add_edge(e, d)

    dag2 = update_pruned(update_truth(construct_dag(rules),
                                      assertions))
    assert dag == dag2


def test_GoalTree_class():
    rules = {"A": ({"B"}, {"C"}, {"D"}),
             "E": ({"D"},)}
    gt = GoalTree(rules)
    assert FactNode("B") in gt.dag.vertices()

    updated_gt = gt.set({"B": True})
    assert FactNode("B", truth=True) in updated_gt.dag.vertices()
    assert FactNode("A", truth=True) in updated_gt.dag.vertices()


def test_GoalTree_class():
    rules = {"A": tuple(),
             "B": tuple()}
    gt = GoalTree(rules)
    assert solution(gt.dag) == None

    # simple case
    gt2 = gt.set({"A": True})
    assert solution(gt2.dag) == "A"

    # raise if more than one true
    gt3 = gt.set({"A": True, "B": True})
    with pytest.raises(ValueError):
        assert solution(gt3.dag)

    # raise if all false
    gt4 = gt.set({"A": False, "B": False})
    with pytest.raises(ValueError):
        assert solution(gt4.dag)

    # last remaining unknown must be True
    gt5 = gt.set({"A": False})
    assert solution(gt5.dag) == "B"

    rules = {"A": ({"F", "E"},),
             "B": ({"F", "G"},)}
    gt = GoalTree(rules)
    assert solution(gt.dag) == None
    gt = gt.set({"F": True})
    assert solution(gt.dag) == None


def test_update_guaranteed():
    # in this example, F can't be false, so it must be true
    rules = {"A": ({"F", "E"},),
             "B": ({"F", "G"},)}
    gt = GoalTree(rules)
    new_assertions = update_guaranteed(
        gt.dag, gt.assertions, gt.exclusive_groups)
    new_gt = gt.set(new_assertions)
    assert FactNode("F", truth=True) in new_gt.dag.all_terminals()

    # in this example, F can't be true, so it must be false
    rules = {"A": ({"F"}, {"C"}),
             "B": ({"F"}, {"D"})}
    gt = GoalTree(rules)
    new_assertions = update_guaranteed(
        gt.dag, gt.assertions, gt.exclusive_groups)
    new_gt = gt.set(new_assertions)
    assert FactNode("F", truth=False) in new_gt.dag.all_terminals()


def test_backward():
    rules = {"A": ({"F", "E"},),
             "B": ({"F", "G"},)}
    gt = GoalTree(rules)

    assert dag_backward_chain(gt.dag, "A")


if __name__ == "__main__":
    from .spongebob_rules import rules

    assertions = frozendict({"is yellow": True})
    gt = GoalTree(rules)

    # for node in gt.dag.all_terminals():
    #     v = node_value(gt, node)

    from .nlp import sentence_to_question
    for leaf in gt.dag.all_terminals():
        s = leaf.fact
        print(s, "--->", sentence_to_question(s))
