from production import IF, AND, THEN, OR, DELETE, NOT, FAIL


RULES = (
    IF (AND('(?x) is fruit'), THEN('(?x) is apple')),
    IF (AND('(?x) is red'), THEN('(?x) is fruit')),
    )

DATA = ('X is red',)
