Installation Guide
=================

This guide covers the different ways to install NetworkPype.

Requirements
-----------

NetworkPype requires:

* Python 3.13 or higher
* Poetry for dependency management

Basic Installation
----------------

The simplest way to install NetworkPype is using poetry:

.. code-block:: console

   $ poetry add networkpype

This will install NetworkPype and all its dependencies.

Development Installation
----------------------

For development, you'll want to clone the repository and install in development mode:

1. Clone the repository:

   .. code-block:: console

      $ git clone https://github.com/yourusername/networkpype.git
      $ cd networkpype

2. Install dependencies with Poetry:

   .. code-block:: console

      $ poetry install

This will install all dependencies, including development dependencies.

3. Set up pre-commit hooks:

   .. code-block:: console

      $ poetry run pre-commit install

Development Tools
---------------

NetworkPype uses several development tools:

* **Poetry**: Dependency management and packaging
* **Pytest**: Testing framework
* **Ruff**: Linting and code formatting
* **Mypy**: Static type checking
* **Pre-commit**: Git hooks for code quality

These are all installed automatically when you do a development installation.

Verifying Installation
--------------------

To verify your installation:

1. Run the tests:

   .. code-block:: console

      $ poetry run pytest

2. Check type hints:

   .. code-block:: console

      $ poetry run mypy networkpype

3. Check code formatting:

   .. code-block:: console

      $ poetry run ruff check .

All these commands should complete without errors.

Troubleshooting
-------------

Common Issues
~~~~~~~~~~~~

1. Python Version Mismatch:
   
   Make sure you have Python 3.13 or higher installed:

   .. code-block:: console

      $ python --version

2. Poetry Installation:
   
   If poetry is not installed, install it following the `official instructions <https://python-poetry.org/docs/#installation>`_.

3. Dependencies Issues:
   
   Try cleaning poetry's cache:

   .. code-block:: console

      $ poetry cache clear . --all 