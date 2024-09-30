# tip: only use OR alternatives when strictly necessary.
# tip: make sure you provide as much info on the individual level as possible: gender, hair, color

rules = {
    "Spongebob": ({"sponge", "has a square head", "has square pants",
                   'wears a suit', 'is male'},),
    "Stanley": ({"sponge", "has a square head", "has tall body",
                 'wears a suit', 'is male'},),
    "sponge": ({"is yellow", "has holes"},),

    "Squidward": ({'octopus', 'wears a brown t-shirt', 'is male'},),
    "Squilliam": ({'octopus', 'has a thick monobrow', 'is male'},),
    "octopus": ({'doesn\'t have two legs', 'has a narrow face but a wide forehead and mouth'},),

    "starfish": ({'is coral-pink', 'has a cone-shaped head'},
                 {'is coral-pink', 'has red dots across its body'}),
    "Patrick Star": ({'starfish', 'wears only a pair of shorts', 'is male'},),
    "Margie Star": ({'starfish', 'has hair', 'is female'},),
    "Herb Star": ({'starfish', 'has a beard', 'is male'},),

    "crustacean": ({'is red', 'has short, thin legs', 'has large pincers'},),

    "crab": ({'crustacean', 'has extremely tall eyes'},),
    "Mr. Krabs": ({'crab', 'wears a suit', 'is male'},),
    "Betsy Krabs": ({'crab', 'has wrinkles', 'is female'},),
    "Redbeard Krabs": ({'crab', 'has an eyepatch', 'has a beard'},
                       {'crab', 'wears a stripped sailor shirt'}),

    "lobster": ({'crustacean', 'has antennae'},),
    "Larry the Lobster": ({'lobster', 'is male'},),

    "plankton": ({'has only one eye', 'is green', 'has short, thin legs',
                  'has antennae'},),
    "Sheldon J. Plankton": ({'plankton', 'is completely naked', 'is male'},),
    "Granny Plankton": ({'plankton', 'is female', 'has hair', 'has wrinkles'},),

    "computer": ({"has a square head", "doesn't have two legs"},),
    # gender is ambiguous, LOL
    "Karen Plankton": ({'computer', 'has a green line on the monitor'},),
    "Karen 2.0": ({'computer', 'has a red line on the monitor'},
                  {'computer', 'has a slick body', 'is female'})
}

exclusive_groups = ({'sponge', 'octopus', 'starfish', 'crustacean',
                               'plankton', 'computer'},
                    {'is male', 'is female'},
                    {'is red', 'is green', 'is yellow', 'is coral-pink'})


if __name__ == "__main__":
    from frozendict import frozendict
    from .goal_tree import GoalTree
    from .draw_goal_tree import render_DAG

    assertions = frozendict({"is red": False,
                             "sponge": True})
    gt = GoalTree(rules, exclusive_groups, assertions)

    render_DAG(gt.dag)
