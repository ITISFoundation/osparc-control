# Osparc Control

[![PyPI](https://img.shields.io/pypi/v/osparc-control.svg)](https://pypi.org/project/osparc-control/) [![Status](https://img.shields.io/pypi/status/osparc-control.svg)](https://pypi.org/project/osparc-control/) [![Python Version](https://img.shields.io/pypi/pyversions/osparc-control)](https://pypi.org/project/osparc-control) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Tests](https://github.com/ITISFoundation/osparc-control/workflows/Tests/badge.svg)](https://github.com/ITISFoundation/osparc-control/actions?workflow=Tests) [![codecov](https://codecov.io/gh/ITISFoundation/osparc-control/branch/master/graph/badge.svg?token=3P04fQlaEb)](https://codecov.io/gh/ITISFoundation/osparc-control) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit) [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Installation

You can install _Osparc Control_ via [pip] from [PyPI]:

```bash
pip install osparc-control
```

## Documentation

Read docs at https://itisfoundation.github.io/osparc-control

## Examples

To run below examples either clone the repo or copy code from the snippets
below the commands

### Simple example

A first example where `requester.py` asks for a random number and
`replier.py` defines an interface to provide it.

- In a first terminal run:

```bash
python examples/1_simple/requester.py
```

#### examples/1_simple/requester.py

[filename](examples/1_simple/requester.py ":include :type=code")

- In a second terminal run:

```bash
python examples/1_simple/replier.py
```

#### examples/1_simple/replier.py

[filename](examples/1_simple/replier.py ":include :type=code")

### Advanced example

A showcase of all the types of supported requests.

- In a first terminal run:

```bash
python examples/2_base_time_add/controller.py
```

#### examples/2_base_time_add/controller.py

[filename](examples/2_base_time_add/controller.py ":include :type=code")

- In a second terminal run:

```bash
python examples/2_base_time_add/solver.py
```

#### examples/2_base_time_add/solver.py

[filename](examples/2_base_time_add/solver.py ":include :type=code")

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].
Our [Code of Conduct] pledge.

## License

Distributed under the terms of the [MIT license],
_Osparc Control_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[cookiecutter]: https://github.com/audreyr/cookiecutter
[mit license]: LICENSE.md
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/ITISFoundation/osparc-control/issues
[pip]: https://pip.pypa.io/
[contributor guide]: CONTRIBUTING.md
[code of conduct]: CODE_OF_CONDUCT.md
