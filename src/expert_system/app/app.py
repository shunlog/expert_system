from flask import Flask, request, url_for, render_template, redirect, send_file
from copy import deepcopy
from dataclasses import replace

from ..goal_tree import eval_goaltree, node_value, GoalTree
from ..draw_goal_tree import render_DAG
from ..spongebob_rules import spongebob_rules
from ..DAG import DAG

app = Flask(__name__)
gt: GoalTree


def reset_tree() -> None:
    global gt
    gt = GoalTree(spongebob_rules)


def set_fact_truth(fact: str, truth: bool):
    global gt
    gt = replace(gt, assertions=gt.assertions.set(fact, truth))


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
    global gt
    data_dag = eval_goaltree(gt)

    render_DAG(data_dag, dir='/tmp/expert_system', fn='diagram')

    facts = []
    for node in data_dag.all_terminals():
        if node.truth is not None or node.pruned:
            continue
        facts.append((node.fact, node_value(gt, node)))
    facts = sorted(facts, key=lambda v: v[1]["roots_cut"], reverse=True)

    return render_template("playground.html", facts=facts)


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
