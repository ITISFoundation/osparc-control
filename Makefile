# Helps setup basic env development

# poetry is required on your system
# suggested installation method
# or refer to official docs
# https://python-poetry.org/docs/
.PHONY: install-poetry
install-poetry:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# install development dependencies as suggested by cookiecutter
# https://cookiecutter-hypermodern-python.readthedocs.io/en/2021.11.26/quickstart.html
.PHONY: install-dev
install-dev:
	pip install nox nox-poetry

.PHONY: tests
tests:	# run tests on lowest python interpreter
	nox -r -s tests -p 3.6

.PHONY: nox-36
nox-36:	# runs nox with python 3.6
	nox -p 3.6

.PHONY: tests-dev
tests-dev:
	pytest -vv -s --exitfirst --failed-first --pdb tests/

.PHONY: docs
docs:	# runs and displays docs
	#runs with py3.6 change the noxfile.py to use different interpreter version
	nox -r -s docs


.PHONY: codestyle
codestyle:	# runs codestyle enforcement
	isort .
	black .

.PHONY: mypy
mypy: # runs mypy
	nox -p 3.6 -r -s mypy
