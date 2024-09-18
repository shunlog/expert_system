from flask import Flask, request, url_for, render_template, redirect, send_file
from copy import deepcopy

from ..goal_tree import GoalTree
from ..draw_goal_tree import render_goal_tree
from ..expert_system import spongebob_tree

app = Flask(__name__)
tree: GoalTree = GoalTree({})


def reset_tree() -> None:
    global tree

    # tree = GoalTree({"penguin": {("bird", "swims", "doesn't fly")},
    #                  "bird": {("feathers",), ("flies", "lays eggs")},
    #                  "albatross": {("bird", "good flyer")}})
    tree = deepcopy(spongebob_tree)


def set_fact_truth(fact: str, truth: bool):
    tree.get_node(fact).set(truth)


@app.route('/pic')
def send_diagram_file():
    return send_file('/tmp/expert_system/diagram.png')


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
    render_goal_tree(tree, dir='/tmp/expert_system', fn='diagram')

    if node := tree.true_hypothesis():
        return render_template("playground.html", true_hypothesis=node.head)

    facts = []
    for node in tree.leaves:
        if node.is_known() or node.is_pruned():
            continue
        fact = node.head
        goalT, goalLast, valH, valL = tree.node_value_parts(fact)
        val = tree.node_value(fact)
        val = round(val, 2) if isinstance(val, float) else val
        facts.append((fact, val, goalT, goalLast,
                      round(valH, 2), round(valL, 2)))
    facts = sorted(facts, key=lambda i: i[1], reverse=True)
    return render_template("playground.html", facts=facts)


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
