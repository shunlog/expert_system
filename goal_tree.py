#!/bin/env python3
from typing import Optional
from collections.abc import Iterable
from copy import deepcopy
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

def or3(ls: Iterable[Optional[bool]]) -> Optional[bool]:
    '''OR a list of booleans which can also be unknown (represented by None)
      # or(true, unknown) = true
      # or(false, unknown) = unknown
    '''
    for v in ls:
        if v:
            return True
        if v is None:
            return None
    return False

def and3(ls: Iterable[Optional[bool]]) -> Optional[bool]:
    '''AND a list of booleans which can also be unknown (represented by None)
      # and(true, unknown) = unknown
      # and(false, unknown) = false
    '''
    for v in ls:
        if v == False:
            return False
        if v is None:
            return None
    return True


class Goal:
    '''
    A Goal represents a node in a Goal tree (a.k.a. and-or tree).

    At its core, a Goal node has three components:
    - `head`: a statement of a fact, like "has feathers"
    - `body`: the subproblems that need to be solved for this goal,
      represented as a set (or-set) of sets (and-sets).
      For leaf nodes, `body` is None.
    - `truth`: a boolean representing whether this fact is true,
      or None if the truthness is unknown.
    
    Every Goal stores references both to the Goal instances from its `body`,
    as well as to its parent Goal nodes from its `parents` field.
    If a Goal has no parents, it is a root node in the tree.
    '''
    head: str
    body: Optional[tuple[tuple["Goal", ...], ...]]
    truth: Optional[bool]
    parents: set["Goal"]
    
    # parents: [Goal]
    def __init__(self, head) -> None:
        self.head = head
        self.body = None
        self.truth = None
        self.parents = set()

    def __repr__(self):
        return f'Goal<{self.head},{self.body}>'

    def set(self, truth: bool) -> None:
        '''Set the truth value of node, and update the parents' values.'''
        self.truth = truth
        for parent in self.parents:
            parent._update()
            
    def _update(self) -> None:
        '''Re-evaluate this node's truth from the children's values,
        and if the value changes, recursively update the parents as well.'''
        old_truth = self.truth
        if not self.body:
            return
        self.truth = or3(and3(n.truth for n in and_set) for and_set in self.body)
        
        if self.truth != old_truth:
            for parent in self.parents:
                parent._update()

                
class GoalTree:
    '''
    A GoalTree groups a set of Goal nodes which might be interconnected.
    It is useful to keep a mapping of all the statements to their existing nodes,
    and to have a list of pointers to root nodes as well as leaf nodes,
    which is what this class is for.
    '''
    
    roots: set[Goal]
    # map a goal's statement (node's head) to the Goal instance.
    node_map: dict[str, Goal] = dict()

    
    # we need to convert all rules into a goal tree in a single function
    # because Goals reference other Goals,
    # so we need to keep a dict, mapping head strings to their respective Goal objects
    def __init__(self, rules: dict[str, tuple[tuple[str, ...], ...]]):
        '''
        - rules: maps every statement to an or-set of and-sets;
            for every statement, one Goal node will be created with all the correct associations;
            if a statement doesn't have a rule for it, it's a leaf node.
        '''
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
            body = tuple(tuple(self.node_map[stmt] for stmt in and_tup) for and_tup in or_tup)
            g.body = body

        # 4. for each goal with a body, add itself as parent of all its children nodes
        for g in self.node_map.values():
            if g.body is None:
                continue
            children_nodes = (n for and_set in g.body for n in and_set)
            for n in children_nodes:
                n.parents.add(g)

        # 5. find all the root nodes (which don't have a parent)
        self.roots = {g for g in self.node_map.values() if len(g.parents) == 0}
        


# updating the values:
# - bottom-up: starting from the leaves, recursively compute sum of the parents' values
# - top-down: set all to 0, then starting from the roots, recursively add values to children
        

def test_init_tree():
    g = GoalTree({"penguin": (("bird", "swims", "doesn't fly"),),
                  "bird": (("feathers",), ("flies", "lays eggs")),
                  "albatross": (("bird", "good flyer"),)})

    assert g.node_map['penguin']
    assert g.node_map['flies']

    # rules
    assert "swims" in [n.head for n in g.node_map['penguin'].body[0]]

    # parents
    bird_parents = [n.head for n in g.node_map['bird'].parents]
    assert ("albatross" in bird_parents and "penguin" in bird_parents)

    # tree roots
    root_heads = [n.head for n in g.roots]
    assert ("albatross" in root_heads and "penguin" in root_heads)



def test_set_truth():
    g = GoalTree({"penguin": (("bird", "swims", "doesn't fly"),),
                  "bird": (("feathers",), ("flies", "lays eggs")),
                  "albatross": (("bird", "good flyer"),)})

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
        
