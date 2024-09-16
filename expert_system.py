from goal_tree import GoalTree
from draw_goal_tree import render_goal_tree


if __name__ == "__main__":    
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})
    


    spongebob_tree = GoalTree({
        "Spongebob": {("sponge", "has square pants")},
        "Stanley": {("sponge", "has tall body")},
        "sponge": {("has a square head", "is yellow", "has holes")},

        "Squidward": {('octopus', 'wears a brown t-shirt')},
        "Squilliam": {('octopus', 'has a thick monobrow')},
        "octopus": {('has tentacles', 'has a big round cranium'),
                    ('has four legs', 'has tentacles')},
        
        "starfish": {()},
        "Patrick": {('starfish',)},
        "Margie": {('starfish',)},
        
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()},
        # "": {()}
    })

    render_goal_tree(spongebob_tree)
