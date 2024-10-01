# Expert system

This is an expert system which functions like Akinator:
you think of a character (that the system knows about),
answer a series of questions
and the system determines the character based on your answers.

It also has an "encyclopedia" mode, in which you pick a character
and it tells you what facts can be used to deduce it.

# Usage

Set up a venv and install deps:
```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Run the web server from inside the `src/` directory:
```sh
python -m expert_system.app.app
```
It should be running at http://127.0.0.1:5000 (check the output).

Run the tests:
```sh
pytest -s expert_system/goal_tree.py
```
