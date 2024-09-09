# TODO: add your imports here:
# from rules import my_rules
from rules_example_zookeeper import ZOOKEEPER_RULES, ZOO_DATA
from production import (forward_chain, backward_chain, match, populate, RuleExpression,
                        IF, THEN, AND, OR, DELETE, simplify, instantiate)
from icecream import ic


def backchain(rules: [IF], hypothesis: str):
    '''
    - rules: iterable of IF rules, following the 3 restrictions
    - hypothesis: a string for which the goal tree will be built
    - returns: either the string `hypothesis`, or the goal tree starting with the OR node
    '''
    def backchain_rule(rule: IF) -> RuleExpression:
        '''Given a matching rule, return the Goal tree formed from it'''
        antecedent = rule.antecedent()
        
        variables_dict = match(rule.consequent()[0], hypothesis)
        def replace_vars(pattern):
            return instantiate(pattern, variables_dict)

        def backchain_clauses(clauses):
            return (backchain(rules, replace_vars(clause)) for clause in clauses)
        
        # Note that we restricted the antecedents to be one of:
        # AND, OR, str
        if isinstance(antecedent, str):
            return replace_vars(antecedent)
        elif isinstance(antecedent, AND):  
            return AND(*backchain_clauses(antecedent))
        elif isinstance(antecedent, OR):
            return OR(*backchain_clauses(antecedent))
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
        return hypothesis
    else:
        return simplify(OR(hypothesis, *(backchain_rule(r) for r in matching_rules)))


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
    expected = OR( 
        'opus is a penguin', 
        AND(
            OR('opus is a bird',
               'opus has feathers',
               AND('opus flies', 'opus lays eggs')),
            'opus does not fly', 
            'opus swims', 
            'opus has black and white color' ))
    
    assert backchain(ZOOKEEPER_RULES, 'opus is a penguin') == expected
    

if __name__=='__main__':
     ic(backchain(ZOOKEEPER_RULES, 'opus is a giraffe'))
