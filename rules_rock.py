from production import IF, AND, THEN, OR, DELETE, NOT, FAIL
from production import forward_chain, backward_chain


# Because:
# (rock beats scissors) AND (scissors beats paper)
# ...
DATA = [ 'rock beats scissors', 
         'scissors beats paper', 
         'paper beats rock' ]

RULES = (
    IF( AND('(?x) beats (?y)', '(?y) beats (?z)'),
        THEN('(?x) beats (?z)') ),
)

if __name__ == '__main__':
    print(DATA)
    DATA2 = forward_chain(RULES, DATA, verbose=True)
    print(DATA2)
