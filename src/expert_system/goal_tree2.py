#!/bin/env python3
from icecream import ic
from .DAG import DAG
from dataclasses import dataclass, field
from typing import Optional

# A GoalTree is represented by a dict:
# the keys are strings representing nodes which in turn represent facts
# the values are sets of tuples, representing


def goal_tree(rules, assertions):
    return DAG()


@dataclass(frozen=True)
class GoalTreeNode:
    true: Optional[bool] = field(default=None, kw_only=True)
    pruned: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class AndNode(GoalTreeNode):
    parent_fact: str
    id: int  # the order in which it appears in the rule definition


@dataclass(frozen=True)
class FactNode(GoalTreeNode):
    fact: str


if __name__ == "__main__":
    g = ({"penguin": (("bird", "swims"),),
          "bird": (("feathers",), ("flies",)),
          "albatross": (("bird", "good flyer"),)})

    def big_dag():
        dag = DAG()

        dag.add_vertex(FactNode("feathers"))
        dag.add_vertex(FactNode("flies"))
        dag.add_vertex(FactNode("bird"))
        dag.add_vertex(AndNode("bird", 0))
        dag.add_vertex(AndNode("bird", 1))
        dag.add_edge(AndNode("bird", 0), FactNode("feathers"))
        dag.add_edge(AndNode("bird", 1), FactNode("flies"))

        dag.add_vertex(FactNode("penguin"))
        dag.add_vertex(AndNode("penguin", 0))
        dag.add_vertex(FactNode("swims"))
        dag.add_edge(AndNode("penguin", 0), FactNode("swims"))
        dag.add_edge(AndNode("penguin", 0), FactNode("bird"))

        dag.add_vertex(FactNode("albatross"))
        dag.add_vertex(AndNode("albatross", 0))
        dag.add_vertex(FactNode("good flyer"))
        dag.add_edge(AndNode("albatross", 0), FactNode("bird"))
        dag.add_edge(AndNode("albatross", 0), FactNode("good flyer"))
        return dag

    dag1 = big_dag()
    dag2 = big_dag()

    assert dag1 == dag2
    dag2.remove_edge(AndNode("albatross", 0), FactNode("good flyer"))
    assert dag1 != dag2
