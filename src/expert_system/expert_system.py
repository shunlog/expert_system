from .goal_tree import GoalTree
from .draw_goal_tree import render_goal_tree

spongebob_tree = GoalTree({
    "Spongebob": {("sponge", "has square pants", 'wears a suit'), },
    "Stanley": {("sponge", "has tall body", 'wears a suit')},
    "sponge": {("has a square head", "is yellow", "has holes")},

    "Squidward": {('octopus', 'wears a brown t-shirt')},
    "Squilliam": {('octopus', 'has a thick monobrow')},
    "octopus": {('has tentacles', 'has a narrow face but a wide forehead and mouth'),
                ('has four legs', 'has tentacles')},

    "starfish": {('is coral-pink', 'has a cone-shaped head'),
                 ('is coral-pink', 'has red dots across its body')},
    "Patrick Star": {('starfish', 'wears only a pair of shorts')},
    "Margie Star": {('starfish', 'has hair')},
    "Herb Star": {('starfish', 'has a beard')},

    "crustacean": {('is red', 'has short, thin legs', 'has large pincers')},

    "crab": {('crustacean', 'has extremely tall eyes')},
    "Mr. Krabs": {('crab', 'wears a suit')},
    "Betsy Krabs": {('crab', 'has wrinkles', 'is female')},
    "Redbeard Krabs": {('crab', 'has an eyepatch', 'has a beard'),
                       ('crab', 'wears a stripped sailor shirt')},

    "lobster": {('crustacean', 'has antennae')},
    "Larry the Lobster": {('lobster',)},

    "plankton": {('is green', 'has short, thin legs', 'has antennae'),
                 ('has only one eye',)},
    "Sheldon J. Plankton": {('plankton', 'is completely naked')},
    "Granny Plankton": {('plankton', 'has wrinkles'),
                        ('plankton', 'is female'),
                        ('plankton', 'has hair')},

    "computer": {("has a square head", "is not organic"), },
    "Karen Plankton": {('computer', 'has a green line on the monitor')},
    "Karen 2.0": {('computer', 'has a red line on the monitor'),
                  ('computer', 'has a slick body')},
})

if __name__ == "__main__":
    render_goal_tree(spongebob_tree)
