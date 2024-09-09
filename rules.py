from production import IF, AND, THEN, OR, DELETE, NOT, FAIL


MY_RULES = (
    IF (AND('(?x) is 1', '(?x) is 2' ), THEN('(?x) is A')),
    IF (AND('(?x) is 1', '(?x) is 3'),
        THEN('(?x) is B')),
    )

MY_DATA = ('a is 10', 'a is 2',
           'b is 1', 'b is 3')
