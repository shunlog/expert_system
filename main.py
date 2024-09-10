# TODO: add your imports here:
# from rules import my_rules
from rules_example_zookeeper import ZOOKEEPER_RULES, ZOO_DATA
from production import (forward_chain, backward_chain, match, populate, RuleExpression,
                        IF, THEN, AND, OR, DELETE, simplify, instantiate)
from collections import defaultdict
from icecream import ic



class GoalTree():
    '''
    A GoalTree instance represents a node with all its antecedents in a goal tree.
    A GoalTree has two parts:
    1. node: the string that represents a node in a goal tree, i.e. the consequent
    2. expr: the RuleExpression that represents the antecedents of that node,
             or None if the node is a leaf.
    '''
    def __init__(self, node: str, expr: RuleExpression = None):
        self.node = node
        self.expr = expr

    def __str__(self):
        if not self.expr:
            return self.node
        return {self.node: self.expr.__str__()}

    def __repr__(self):
        return str(self.__str__())

    def compute_cost(self, costs = None):
        if costs == None:
            costs = defaultdict(lambda : [0.0, 0.0])
            
        if costs[self.node] == [0.0, 0.0]:
            # assuming current node is a root node,
            # so giving it an initial value
            costs[self.node] = [1.0, 1.0]
        
        cost = costs[self.node]
        
        if self.expr is None:
            pass

        elif isinstance(self.expr, AND):
            yes_cost = cost[0] / len(self.expr)  # all needed for True
            no_cost = cost[1]  # one enough for False
            for clause in self.expr:
                assert(isinstance(clause, GoalTree))
                costs[clause.node][0] += yes_cost
                costs[clause.node][1] += no_cost
                clause.compute_cost(costs)

        elif isinstance(self.expr, OR):
            OR_yes_cost = cost[0]  # one enough for True
            OR_no_cost = cost[1] / len(self.expr)  # all needed for False

            for or_clause in self.expr:
                if isinstance(or_clause, GoalTree):
                    costs[or_clause.node][0] += OR_yes_cost
                    costs[or_clause.node][1] += OR_no_cost
                    or_clause.compute_cost(costs)
                    
                elif isinstance(or_clause, AND):
                    AND_yes_cost = OR_yes_cost / len(or_clause)  # all needed for True
                    AND_no_cost = OR_no_cost  # one enough for False
                    for and_clause in or_clause:
                        assert(isinstance(and_clause, GoalTree))
                        costs[and_clause.node][0] += AND_yes_cost
                        costs[and_clause.node][1] += AND_no_cost
                        and_clause.compute_cost(costs)

        else:
            raise("Invalid GoalTree expr", self.expr)

        return costs
        

def backchain(rules: [IF], hypothesis: str) -> GoalTree:
    '''
    - rules: iterable of IF rules, following the 3 restrictions:
        1. You will never have to test a hypothesis with unknown variables.
           All variables that appear in the  antecedent
           will also appear in the consequent.
        2. All assertions are positive: no rules will have DELETE parts or NOT clauses.
Antecedents are not nested. Something like (OR (AND x y) (AND z w)) will not appear 
in the antecedent parts of rules
    - hypothesis: a string for which the goal tree will be built
    - returns: either the string `hypothesis`, or the goal tree starting with the OR node
    '''
    def backchain_rule(rule: IF) -> RuleExpression:
        '''Given a matching rule, return the Goal tree formed from it'''
        antecedent = rule.antecedent()
        
        if isinstance(antecedent, str):
            return antecedent
        
        # Note that we restricted the antecedents to be one of:
        # AND, OR, str
        variables_dict = match(rule.consequent()[0], hypothesis)
        instantiated_clauses = [instantiate(clause, variables_dict) for clause in antecedent]
        if len(instantiated_clauses) == 1:
            return backchain(rules, instantiated_clauses[0])
        elif isinstance(antecedent, AND):
            return AND(*(backchain(rules, clause) for clause in instantiated_clauses))
        elif isinstance(antecedent, OR):
            return OR(*(backchain(rules, clause) for clause in instantiated_clauses))
        else:
            assert False

    def rule_matches(rule: IF) -> bool:
        '''Return True if the hypothesis matches the rule's consequent
        '''
        # note that a THEN consequent is a list of patterns,
        # but we constrain our rules to have a single consequent pattern,
        # therefore we only check the first one
        assert len(rule.consequent()) == 1
        pattern = rule.consequent()[0]
        return match(pattern, hypothesis) is not None
    
    matching_rules = [r for r in rules if rule_matches(r)]
    if len(matching_rules) == 0:
        return GoalTree(hypothesis)
    else:
        if len(matching_rules) == 1:
            expr = backchain_rule(matching_rules[0])
        else:
            expr = OR([backchain_rule(r) for r in matching_rules])
        return GoalTree(hypothesis, expr)


def test_leaf_node():
    assert backchain([], 'no matching rules') == 'no matching rules'


def test_one_AND_rule():
    # this also tests if the simplification is happening
    rules = (IF(AND('flies'), THEN('is a bird')),)
    assert backchain(rules, 'is a bird') == \
        OR('is a bird', 'flies')


def test_one_simple_rule():
    rules = (IF('flies', THEN('is a bird')),)
    assert backchain(rules, 'is a bird') == \
        OR('is a bird', 'flies')


def test_two_simple_rules():
    rules = (IF('flies', THEN('is a bird')),
             IF('has feathers', THEN('is a bird')),)
    assert backchain(rules, 'is a bird') == \
        OR('is a bird', 'flies', 'has feathers')
    

def test_AND_rule_with_multiple_clauses():
    rules = (IF(AND('flies', 'has feathers'), THEN('is a bird')),)
    assert backchain(rules, 'is a bird') == \
        OR('is a bird', AND('flies', 'has feathers'))


def test_AND_plus_simple_rule():
    rules = (IF(AND('flies', 'lays eggs'), THEN('is a bird')),
             IF('has feathers', THEN('is a bird')),)
    # the order in the output should match the order of the rules
    assert backchain(rules, 'is a bird') == \
        OR('is a bird',
           AND('flies', 'lays eggs'),
           'has feathers')


def test_variable_instantiation():
    rules = (IF('(?x) flies', THEN('(?x) is a bird')),)
    assert backchain(rules, 'Pingu is a bird') == \
        OR('Pingu is a bird', 'Pingu flies')

    
    
def test_ZOO_example():
    # nested example, traversing all the possible code paths

    # The original exercise asks for this representation of the goal tree:
    # expected = OR( 
    #     'opus is a penguin', 
    #     AND(
    #         OR('opus is a bird',
    #            'opus has feathers',
    #            AND('opus flies', 'opus lays eggs')),
    #         'opus does not fly', 
    #         'opus swims', 
    #         'opus has black and white color' ))
    # but this representation makes it difficult to tell what are the intermediate facts
    # and what are their definition rules.
    # My GoalTree data structure solves this issue.

    
    expected = \
    {"opus is a penguin": {
        "AND": [
        {
            "opus is a bird": {
                "OR": [
                    "opus has feathers",
                    {
                        "AND": [
                            "opus flies",
                            "opus lays eggs"
                        ]
                    }
                 ]
            }
        },
        "opus does not fly",
        "opus swims",
        "opus has black and white color"]}}

    '''
    (0) Opus is a penguin
      - Opus is a bird (1) and Opus does not fly and Opus swims
    (1) Opus is a bird
      - Opus has feathers, or
      - Opus fies and Opus lays eggs
    '''
    
    assert backchain(ZOOKEEPER_RULES, 'opus is a penguin') == expected
    

if __name__=='__main__':
    
    # goal_tree = backchain(ZOOKEEPER_RULES, 'opus is a penguin')
    # goal_obj = goal_tree.__str__()
    # import json
    # print(json.dumps(goal_obj, indent=4))

    costs = None
    hypotheses = ('X is a penguin',
                  'X is a ostrich',
                  'X is a zebra',
                  'X is a giraffe',
                  'X is a cheetah',
                  'X is a tiger',
                  'X is a albatross')
    for hypothesis in hypotheses:
        goal_tree = backchain(ZOOKEEPER_RULES, hypothesis)
        costs = goal_tree.compute_cost(costs)
    ic(costs)


    avg_costs = dict()
    middle_score = len(hypotheses) / 2
    for k, v in costs.items():
        avg_value = (v[0] - middle_score) ** 2 + (v[1] - middle_score) ** 2
        avg_costs[k] = avg_value
    ic(sorted(avg_costs.items(), key = lambda v: v[1]))
    
    

