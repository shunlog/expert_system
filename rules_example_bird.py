from production import IF, AND, THEN, OR, DELETE, NOT, FAIL

RULES = ( IF( AND( '(?x) has feathers',  # rule 1
                   '(?x) has a beak' ),
              THEN( '(?x) is a bird' )),
          IF( AND( '(?y) is a bird',     # rule 2
                 '(?y) cannot fly',
                 '(?y) can swim' ),
            THEN( '(?y) is a penguin' ) ) )


# For each rule, we test the antecedents,
# And if they match any of the data, we try to fire them.
# They won't fire if there's no THEN or DELETE clauses,
# or if the data to be created already exists

DATA = ( 'Pendergast is a penguin',
         'Pendergast has feathers',
         'Pendergast has a beak',
         'Pendergast cannot fly',
         'Pendergast can swim' )
