from production import IF, AND, THEN, OR, DELETE, NOT, FAIL
from production import forward_chain, backward_chain
from icecream import ic

# You will be given data that includes three kinds of statements:  
#   - 'male x': x is male  
#   - 'female x': x is female  
#   - 'parent x y': x is a parent of y
# Every person in the data set will be defined to be either male or female.  

# Your task is to deduce, wherever you can, the following relations:  
#   - 'brother x y': x is the brother of y (sharing at least one parent)  
#   - 'sister x y': x is the sister of y (sharing at least one parent)  
#   - 'mother x y': x is the mother of y  
#   - 'father x y': x is the father of y  
#   - 'son x y': x is the son of y  
#   - 'daughter x y': x is the daughter of y  
#   - 'cousin x y': x and y are cousins (a parent of x and a parent of y are siblings)  
#   - 'grandparent x y': x is the grandparent of y  
#   - 'grandchild x y': x is the grandchild of y

# Some examples to try it on:
simpsons_data = ("male bart",
                 "female lisa",
                 "female maggie",
                 "female marge",
                 "male homer",
                 "male abe",
                 "parent marge bart",
                 "parent marge lisa",
                 "parent marge maggie",
                 "parent homer bart",
                 "parent homer lisa",
                 "parent homer maggie",
                 "parent abe homer")

rules = (
    # mother
    IF (AND('parent (?mom) (?x)',
            'female (?mom)'),
        THEN('mother (?mom) (?x)')),

    # father relation
    IF (AND('parent (?dad) (?x)',
            'male (?dad)'),
        THEN('father (?dad) (?x)')),

    # same-identity  (hack needed for sibling)
    IF ('male (?x)',
        THEN('same-identity (?x) (?x)')),
    IF ('female (?x)',
        THEN('same-identity (?x) (?x)')),

    # sibling relation
    IF (AND('parent (?p) (?child2)',
            'parent (?p) (?child1)',
            NOT('same-identity (?child1) (?child2)')),
        THEN('siblings (?child1) (?child2)')),

    # brother
    IF( AND('siblings (?brother) (?x)',
            'male (?brother)'),
        THEN('brother (?brother) (?x)')),
    
    # sister
    IF( AND('siblings (?sister) (?x)',
            'female (?sister)'),
        THEN('sister (?sister) (?x)'))

    # daughter...

    # son...

    # grandparent...

    # grandchild...

    # cousin...
)

if __name__ == '__main__':
    ic(simpsons_data)
    data2 = forward_chain(rules, simpsons_data, verbose=True)
    diff = set(data2) - set(simpsons_data)
    ic(diff)
