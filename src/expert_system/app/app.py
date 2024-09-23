from flask import Flask, request, url_for, render_template, redirect, send_file
from copy import deepcopy

from ..goal_tree import construct_dag, update_truth
from ..draw_goal_tree import render_DAG
from ..spongebob_rules import spongebob_rules
from ..DAG import DAG

app = Flask(__name__)
dag: DAG = construct_dag({})
assertions: dict[str, bool] = {}


def reset_tree() -> None:
    global dag
    dag = construct_dag(spongebob_rules)


def set_fact_truth(fact: str, truth: bool):
    assertions[fact] = truth
    reset_tree()
    global dag
    dag = update_truth(dag, assertions)


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
    render_DAG(dag, dir='/tmp/expert_system', fn='diagram')

    facts = []
    for node in dag.all_terminals():
        if node.truth is not None or node.pruned:
            continue
        facts.append(node.fact)

    return render_template("playground.html", facts=facts)


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
