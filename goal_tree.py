#!/bin/env python3
from typing import Optional, Union
from collections import defaultdict
from collections.abc import Sequence, Collection, Iterable
from copy import deepcopy
from three_valued_logic import and3, or3

from icecream import ic

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
        
    def set(self, truth: bool) -> None:
        '''Set the truth value of node, and call _update()'''
        self.truth = truth
        self._update(False)

    def eval_body(self) -> Union[bool, None]:
        '''Evaluate the truth of this node according to the rules in the body.
        If this is a leaf node, return None'''
        if not self.body:
            return None
        return or3([and3([n.truth for n in and_set]) for and_set in self.body])
        
    def _update(self, re_eval:bool = True) -> None:
        '''
        When the truth value of a node becomes known, there are multiple things that need to happen:
        - re-evaluate the parents' values
        - prune links to children
        - if new value is False, prune and-sets which contain the current node in parents
        
        This function re-evaluates this node's truth according to its body,
        and if the value changes, recursively updates the parents as well.
        If `re_eval` is False, assume the truth has just been changed,
        so don't evaluate it but simply do all the necessary updates.'''
        if re_eval:
            truth = self.eval_body()
            if truth == self.truth:
                # value hasn't changed, don't do anything
                return
            self.truth = truth

        # 1. prune children branches

        # 2. prune and-sets branches in parents
    
        # 3. update the parents
        for parent in self.parents:
            parent._update()

            
class GoalTree:
    '''
    A GoalTree groups a set of Goal nodes which might be interconnected.
    It is useful to keep a mapping of all the statements to their existing nodes,
    and to have a list of pointers to root nodes as well as leaf nodes,
    which is what this class is for.
    '''

    leaves: set[Goal]
    roots: set[Goal]
    # map a goal's statement (node's head) to the Goal instance.
    node_map: dict[str, Goal]

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
            body = set(tuple(self.node_map[stmt] for stmt in and_tup) for and_tup in or_tup)
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

        
    def leaf_nodes_values(self) -> dict[Goal, float]:
        '''
        Computes a value for each leaf node, such that the higher the value,
        the more evenly a question will split the hypotheses into two halves.

        Procedure:
        1. set every node's value to 0, except for root nodes, which have a default value
        2. Go top-down recursively from the root nodes,
           adding their contribution to their children nodes.
        3. When finished, return the values of leaf nodes

        You could also do this bottom-up, but it would be more complicated.
        In bottom-up, you have to memoize:
        1. unknown-count(and-set) and unknown_count(or-set)
        2. value(node), needed multiple times
        In top-down, you only have to keep track of each node's accumulator value.

        Actually can't go top-down because before adding values to the children of node X,
        you need to make sure X's value won't change,
        but for that you need to make sure all its parents have been processed,
        which is exactly bottom-up.

        We want to sort nodes:
        - first, by how many root nodes they influence
          - the closer it gets to 50%, the better
          - note: excluding paths in which they make no difference
        - second, by how close they are to root nodes
          - for this i can use my value splitting procedure
        '''
        
        # node_values_map: dict[Goal, tuple[float, float]] = defaultdict(lambda: (0, 0))
        # root_value = 1 / len(self.roots)

        # def process_node(node: Goal) -> None:
        #     '''Add values to node's children, then process the children recursively.'''
        #     return node_value_map
            
        return {}

    
def test_init_tree():
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})

    assert g.node_map['penguin']
    assert g.node_map['flies']

    # rules
    assert "swims" in [n.head for n in g.node_map['penguin'].body.pop()]

    # parents
    bird_parents = [n.head for n in g.node_map['bird'].parents]
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
    g2.node_map["feathers"].set(True)
    assert g2.node_map["feathers"].truth == True
    assert g2.node_map["bird"].truth == True
    assert g2.node_map["albatross"].truth == None

    g3 = deepcopy(g)
    g3.node_map["feathers"].set(False)
    assert g3.node_map["bird"].truth is None
    g3.node_map["flies"].set(True)
    assert g3.node_map["bird"].truth is None
    g3.node_map["lays eggs"].set(True)
    assert g3.node_map["bird"].truth == True
    g3.node_map["good flyer"].set(True)

    
