from flask import Flask, request, url_for, render_template, redirect, send_file
from copy import deepcopy
from dataclasses import replace

from ..goal_tree import construct_dag, update_truth, update_pruned, full_dag, node_value, \
    GoalTreeData
from ..draw_goal_tree import render_DAG
from ..spongebob_rules import spongebob_rules
from ..DAG import DAG

app = Flask(__name__)
data: GoalTreeData


def reset_tree() -> None:
    global data
    data = GoalTreeData(spongebob_rules)


def set_fact_truth(fact: str, truth: bool):
    global data
    data = replace(data, assertions=data.assertions.set(fact, truth))


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
    global data
    dag = full_dag(data)

    render_DAG(dag, dir='/tmp/expert_system', fn='diagram')

    facts = []
    for node in dag.all_terminals():
        if node.truth is not None or node.pruned:
            continue
        facts.append((node.fact, node_value(data, node)))
    facts = sorted(facts, key=lambda v: v[1]["roots_cut"], reverse=True)

    return render_template("playground.html", facts=facts)


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
