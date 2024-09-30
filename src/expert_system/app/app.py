from flask import Flask, request, url_for, render_template, redirect, send_file
from copy import deepcopy
from dataclasses import replace

from ..goal_tree import node_value, GoalTree, solution
from ..draw_goal_tree import render_DAG
from ..DAG import DAG

from ..spongebob_rules import rules, exclusive_groups
# from ..zoo_rules import rules, exclusive_groups

app = Flask(__name__)
gt: GoalTree


def rated_facts() -> list[tuple[str, dict]]:
    facts = []
    for node in gt.dag.all_terminals():
        if node.truth is not None or node.pruned:
            continue
        facts.append((node.fact, node_value(gt, node)))
    return sorted(facts, key=lambda v: v[1]
                  ["value"], reverse=True)


def reset_tree() -> None:
    global gt
    gt = GoalTree(rules, exclusive_groups)


def set_fact_truth(fact: str, truth: bool):
    global gt
    gt = gt.set({fact: truth})


@app.route('/pic')
def send_diagram_file():
    return send_file('/tmp/expert_system/diagram.svg')


@app.post('/reset')
def reset_tree_view():
    reset_tree()
    return redirect(request.referrer or '/')


@app.post('/answer')
def set_truth_view():
    truth = request.form['truth'] == 'true'
    fact = request.form['fact']
    set_fact_truth(fact, truth)
    return redirect(request.referrer or '/')


@app.route("/akinator")
def akinator_view():
    global gt
    if sol := solution(gt.dag):
        return render_template("akinator.html", solution=sol)
    fact = rated_facts()[0][0]
    return render_template("akinator.html", fact=fact)


@app.route("/playground")
def playground_view():
    global gt
    render_DAG(gt.dag, dir='/tmp/expert_system', fn='diagram', format="svg")
    if sol := solution(gt.dag):
        return render_template("playground.html", solution=sol)
    return render_template("playground.html", fact_values=rated_facts())


@app.route("/")
def root_view():
    return f'''
    <li><a href={url_for("playground_view")}>Playground</a></li>
    <li><a href={url_for("akinator_view")}>Akinator mode</a></li>
    <li><a>Encyclopedia mode</a></li>
    '''


if __name__ == '__main__':
    reset_tree()
    app.run(debug=True)
