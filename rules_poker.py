from production import IF, AND, THEN, OR, DELETE, NOT, FAIL
from production import forward_chain, backward_chain

# You're given this data about poker hands:
DATA = ( 'two-pair beats pair',
         'three-of-a-kind beats two-pair',
         'straight beats three-of-a-kind',
         'flush beats straight',
         'full-house beats flush',
         'straight-flush beats full-house' )

# Fill in this rule so that it finds all other combinations of
# which poker hands beat which, transitively. For example, it
# should be able to deduce that a three-of-a-kind beats a pair,
# because a three-of-a-kind beats two-pair, which beats a pair.
RULES = (
    IF( AND('(?x) beats (?y)', '(?y) beats (?z)'),
        THEN('(?x) beats (?z)') ),
)

if __name__ == '__main__':
    print(DATA)
    DATA2 = forward_chain(RULES, DATA, verbose=True)
    print(DATA2)
