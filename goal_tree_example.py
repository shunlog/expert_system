from goal_tree import GoalTree
from draw_goal_tree import render_goal_tree


if __name__ == "__main__":
    g = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})
    
    render_goal_tree(g)
