#!/bin/env python3
from typing import Optional, Union, Self
from collections import defaultdict
from collections.abc import Sequence, Collection, Iterable
from copy import deepcopy
from icecream import ic

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
To store the knowledge, each node will keep track of its truth value,
which can be true, false, or unknown.
This is enough data since we are dealing with only one subject at a time.
The way a goal tree acts as an inference engine is pretty obvious.

There are two kinds of rule-based systems:
    - Production systems, which use if-then rules to derive actions from conditions.
    - Logic programming systems, which use conclusion if conditions rules to derive
      conclusions from conditions.
As opposed to production systems where we only need to provide data as a list of facts that are true,
in an expert system we need to be able to represent that a statement is false
for the optimization of asking questions and deducing facts.
'''


class Goal:
    '''
    A Goal represents a node in a Goal tree (a.k.a. and-or tree).

    At its core, a Goal node has three components:
    - `head`: a statement of a fact, like "has feathers"
    - `body`: the subproblems that need to be solved for this goal,
      represented as a set (or-set) of sets (and-sets).
      For leaf nodes, `body` has 0 elements.
    - `truth`: a boolean representing whether this fact is true,
      or None if the truthness is unknown.

    Every Goal stores references both to the Goal instances from its `body`,
    as well as to its parent Goal nodes from its `parents` field.
    If a Goal has no parents, it is a root node in the tree.
    '''
    head: str
    body: set[tuple["Goal", ...]]
    truth: Optional[bool]
    parents: set["Goal"]

    def __init__(self, head) -> None:
        self.head = head
        self.body = set()
        self.truth = None
        self.parents = set()

    def __repr__(self):
        return f'Goal<{self.head},{self.body}>'

    def is_leaf(self) -> bool:
        return len(self.body) == 0

    def is_root(self) -> bool:
        return len(self.parents) == 0

    def is_known(self) -> bool:
        return self.truth is not None

    def children(self) -> set["Goal"]:
        '''Return an set of all the children mentioned in the body.'''
        return set(node for and_set in self.body for node in and_set)

    def set(self, truth: bool) -> None:
        '''Set the truth value of node and re-evaluate the parents'''
        self.truth = truth
        for parent in self.parents:
            parent._update()

    def eval_body(self) -> Union[bool, None]:
        '''Evaluate the truth of this node according to the rules in the body.
        If this is a leaf node, return None'''
        if not self.body:
            return None
        return or3([and3([n.truth for n in and_set]) for and_set in self.body])

    def _update(self) -> None:
        '''
        When the truth of a node changes we need to re-evaluate the parents recursively.
        '''
        truth = self.eval_body()
        if truth == self.truth:
            # value hasn't changed, no need to re-evaluate further up
            return
        self.truth = truth
        for parent in self.parents:
            parent._update()

    def is_pruned(self) -> bool:
        '''
        A node is "pruned" when we don't care to find out its truth value.
        This is useful for minimizing the number of questions asked.
        For example, a node can be pruned if:
        - all its parents' truth values have become known, or
        - it was in a single and-set with a node that has become False,
          so now the entire and-set is false, so this node's value doesn't matter anymore

        A node is pruned if each of its forward links either:
        1. links to a False and-set, or
        2. is leading to a parent that is pruned, or
        3. is leading to a parent whose truth is known
        '''
        # TODO add that node is pruned if it's contained in all the and-sets of the remaining roots
        # need the entire Tree for that, to check if there are any other remaining roots
        if self.is_known():
            return False

        def pruned_parent(parent: Goal) -> bool:
            a = parent.is_pruned()
            c = parent.is_known()

            def false_and_set(and_set):
                return any(n.truth == False for n in and_set)
            b = all(false_and_set(and_set)
                    for and_set in parent.body if self in and_set)
            return a or b or c

        if not self.parents:
            return False

        return all(pruned_parent(p) for p in self.parents)


class GoalTree:
    '''
    A GoalTree groups a set of Goal nodes which might be interconnected.

    This class makes it easy to get a node object representing a statement,
    and it makes it possible to group multiple root nodes.
    '''
    leaves: set[Goal]
    roots: set[Goal]
    # map a statement to its respective Goal instance.
    node_map: dict[str, Goal]

    def get_node(self, statement: str) -> Goal:
        return self.node_map[statement]

    # we need to convert all rules into a goal tree in a single function
    # because Goals reference other Goals,
    # so we need to keep a dict, mapping head strings to their respective Goal objects

    def __init__(self, rules: dict[str, set[tuple[str, ...]]]):
        '''
        - rules: maps every statement to an or-set of and-sets;
            for every statement, one Goal node will be created with all the correct associations;
            if a statement doesn't have a rule for it, it's a leaf node.
        '''
        self.node_map = dict()

        # 1. create all the intermediate nodes (which have a production rule)
        for statement in rules:
            g = Goal(statement)
            self.node_map[statement] = g

        # 2. create all the leaf nodes
        for or_set in rules.values():
            for and_set in or_set:
                for statement in and_set:
                    if self.node_map.get(statement) is not None:
                        continue
                    g = Goal(statement)
                    self.node_map[statement] = g

        # 3. for each Goal, add the body with references to other goals
        for g in self.node_map.values():
            or_tup = rules.get(g.head)
            if or_tup is None:
                continue  # it is a leaf node, with no body
            body = set(tuple(self.get_node(stmt) for stmt in and_tup)
                       for and_tup in or_tup)
            g.body = body

        # 4. for each goal with a body, add itself as parent of all its children nodes
        for g in self.node_map.values():
            if g.body is None:
                continue
            for and_set2 in g.body:
                for n in and_set2:
                    n.parents.add(g)

        # 5. find all the root nodes (with no parents)
        # and all leaf nodes (with no children/body)
        self.roots = {g for g in self.node_map.values() if g.is_root()}
        self.leaves = {g for g in self.node_map.values() if g.is_leaf()}

    def node_value_parts(self, fact: str) -> tuple[bool, bool, float, float]:
        '''
        Computes the parameters that define the questioning value of a leaf node.
        Return values:
        1. GoalT - true if done when answered True
        2. GoalF - true if done when answered False
        3. ValueH - the fraction of hypotheses proven False when the answer is F.
           In the range [0, 1], the bigger the better.
        4. ValueL - the average fraction of pruned leaves when the answer is T and when it is F.
           In the range [0, 1], the bigger the better.

        It's not clear what parameters to prioritize, or whether this strategy is good at all.
        '''
        def pruned_cnt(tree: GoalTree) -> int:
            return sum(1 for l in tree.leaves if l.is_pruned())

        def false_hypoth_cnt(tree: GoalTree) -> int:
            return sum(1 for n in tree.roots if n.truth == False)

        # initial state
        pruned_initially = pruned_cnt(self)
        false_initially = false_hypoth_cnt(self)

        # if the answer is True
        tree_T = deepcopy(self)
        tree_T.get_node(fact).set(True)
        pruned_T = pruned_cnt(tree_T) - pruned_initially
        goalT = tree_T.check_result() is not None

        # if the answer is False
        tree_F = deepcopy(self)
        tree_F.get_node(fact).set(False)
        pruned_F = pruned_cnt(tree_F) - pruned_initially
        false_hypoth = false_hypoth_cnt(tree_F)
        goalF = tree_F.check_result() is not None

        valH = (false_hypoth - false_initially) / len(self.roots)
        valL = (pruned_T + pruned_F) / 2 / len(self.leaves)
        return (goalT, goalF, valH, valL)

    def node_value(self, fact: str) -> Union[Goal, float]:
        '''Computes the node questioning value by combining the parts.
        Prioritize questions that lead to being done.'''
        goalT, goalF, valH, valL = self.node_value_parts(fact)
        if goalT and goalF:
            # unlikely, but still worth prioritizing
            return 1000
        elif goalT or goalF:
            return 999

        return valH + valL

    def check_result(self, ) -> Optional[Goal]:
        '''
        Check if a hypothesis was found to be true,
        or if there is only one remaining, meaning it has to be the one.
        Also assert that there is always one and only one answer.
        '''
        true_roots = [r for r in self.roots if r.truth]
        # TODO uncomment this when the pruning is completed
        # assert len(true_roots) < 2
        if true_roots:
            return true_roots[0]

        unknown_roots = [r for r in self.roots if r.truth is None]
        # TODO uncomment this when the pruning is completed
        # assert len(unknown_roots) != 0  # can't have all be False
        if len(unknown_roots) == 1:
            return unknown_roots[0]
        return None


def test_init_tree():
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})

    assert g.get_node('penguin')
    assert g.get_node('flies')
    # rules
    assert "swims" in [n.head for n in g.get_node('penguin').body.pop()]
    # parents
    bird_parents = [n.head for n in g.get_node('bird').parents]
    assert ("albatross" in bird_parents and "penguin" in bird_parents)
    # tree roots
    root_heads = [n.head for n in g.roots]
    assert ("albatross" in root_heads and "penguin" in root_heads)


def test_set_truth_bubbles_upward():
    # test that setting the truth of a node
    # updates the truth of its parents
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})

    g2 = deepcopy(g)
    g2.get_node("feathers").set(True)
    assert g2.get_node("feathers").truth == True
    assert g2.get_node("bird").truth == True
    assert g2.get_node("albatross").truth == None

    g3 = deepcopy(g)
    g3.get_node("feathers").set(False)
    # Or(False, None) = None
    assert g3.get_node("bird").truth is None
    # And(True, None) = None
    g3.get_node("flies").set(True)
    assert g3.get_node("bird").truth is None
    g3.get_node("lays eggs").set(True)
    assert g3.get_node("bird").truth == True
    g3.get_node("good flyer").set(True)

    g4 = deepcopy(g)
    g4.get_node("feathers").set(False)
    g4.get_node("lays eggs").set(False)
    assert g4.get_node("bird").truth == False


def test_pruned_nodes():
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer"),
                                ("bird", "long beak")}})

    # parent's value is known
    g2 = deepcopy(g)
    assert g2.get_node("penguin").is_pruned() == False  # test root node
    assert g2.get_node("flies").is_pruned() == False
    g2.get_node("bird").set(True)
    assert g2.get_node("flies").is_pruned() == True
    # known nodes are not considered pruned
    assert g2.get_node("bird").is_pruned() == False

    # link is pruned because of a False node in the same and-set
    g3 = deepcopy(g)
    assert g3.get_node("flies").is_pruned() == False
    g3.get_node("lays eggs").set(False)
    assert g3.get_node("flies").is_pruned() == True

    # all links must be pruned
    # in this case, "bird" is in 2 and-sets of parent "albatross"
    # and in one and-set of parent "penguin"
    g4 = deepcopy(g)
    g4.get_node("swims").set(False)
    assert g4.get_node("bird").is_pruned() == False
    g4.get_node("long beak").set(False)
    assert g4.get_node("bird").is_pruned() == False
    g4.get_node("good flyer").set(False)
    assert g4.get_node("bird").is_pruned() == True
    # test recursion
    assert g4.get_node("flies").is_pruned() == True


def test_node_value():
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})

    # "flies" needs "lays eggs" to achieve the same as "feathers" alone
    assert g.node_value('feathers') > g.node_value('flies')
