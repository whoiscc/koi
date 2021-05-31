To setup, with Python 3.8.5, in project directory

```
pip install --editable .  # recommand inside venv
```

To regression

```
coverage run --source=src -m unittest test.koi_tests
python -m doctest src/**/*.py
```

To try lexical parser

```
python src/koi/lexer.py misc/<name>.koi
```
