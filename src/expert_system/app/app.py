from flask import Flask, request, url_for, render_template, redirect

from ..goal_tree import GoalTree
from ..draw_goal_tree import render_goal_tree

app = Flask(__name__)
tree: GoalTree = GoalTree({})


def reset_tree() -> None:
    global tree
    tree = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
                  "bird": {("feathers",), ("flies", "lays eggs")},
                  "albatross": {("bird", "good flyer")}})

    
def set_fact_truth(fact: str, truth: bool):
    tree.get_node(fact).set(truth)


@app.post('/reset')
def reset_tree_view():
    reset_tree()
    return redirect('/')


@app.post('/answer')
def set_truth_view():
    truth = request.form['truth'] == 'true'
    fact = request.form['fact']
    set_fact_truth(fact, truth)
    return redirect('/')


@app.route("/")
def root_view():
    render_goal_tree(tree, dir='src/app/static', fn='diagram')
    facts = [n.head for n in tree.leaves]
    return render_template("playground.html", facts=facts)


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
 
