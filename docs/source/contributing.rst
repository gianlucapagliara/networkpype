Contributing Guide
=================

Thank you for considering contributing to NetworkPype! This document provides guidelines and instructions for contributing.

Development Setup
---------------

1. Fork the Repository
   
   First, fork the repository on GitHub and then clone your fork:

   .. code-block:: console

      $ git clone https://github.com/yourusername/networkpype.git
      $ cd networkpype

2. Set Up Development Environment
   
   We use Poetry for dependency management:

   .. code-block:: console

      $ poetry install
      $ poetry run pre-commit install

Code Style
---------

We follow strict code style guidelines:

* Use type hints for all function arguments and return values
* Follow PEP 8 style guide
* Use docstrings for all public functions and classes (Google style)
* Keep lines under 88 characters
* Use meaningful variable and function names

Example of well-formatted code:

.. code-block:: python

    from typing import List, Optional

    def process_data(
        input_data: List[str],
        max_items: Optional[int] = None
    ) -> List[str]:
        """Process the input data and return filtered results.

        Args:
            input_data: List of strings to process
            max_items: Maximum number of items to return

        Returns:
            List of processed strings

        Raises:
            ValueError: If input_data is empty
        """
        if not input_data:
            raise ValueError("Input data cannot be empty")
        
        result = [item.strip() for item in input_data]
        
        if max_items is not None:
            result = result[:max_items]
        
        return result

Testing
-------

All new features should include tests:

1. Write tests using pytest
2. Ensure 100% test coverage for new code
3. Run the full test suite before submitting:

   .. code-block:: console

      $ poetry run pytest

Type Checking
------------

We use mypy for static type checking:

.. code-block:: console

   $ poetry run mypy networkpype

Code Quality
-----------

Before submitting a pull request:

1. Run Ruff:

   .. code-block:: console

      $ poetry run ruff check .
      $ poetry run ruff format .

2. Run pre-commit hooks:

   .. code-block:: console

      $ poetry run pre-commit run --all-files

Pull Request Process
------------------

1. Create a new branch for your feature:

   .. code-block:: console

      $ git checkout -b feature-name

2. Make your changes and commit them:

   .. code-block:: console

      $ git add .
      $ git commit -m "Description of changes"

3. Push to your fork:

   .. code-block:: console

      $ git push origin feature-name

4. Create a Pull Request on GitHub

   * Use a clear and descriptive title
   * Include a detailed description of changes
   * Reference any related issues

Documentation
------------

When adding new features:

1. Add docstrings to all new functions and classes
2. Update the relevant documentation files
3. Include examples in the docstrings
4. Build and check the documentation:

   .. code-block:: console

      $ cd docs
      $ poetry run make html

Release Process
-------------

1. Version Bumping
   
   We use semantic versioning (MAJOR.MINOR.PATCH):

   * MAJOR version for incompatible API changes
   * MINOR version for new functionality in a backward compatible manner
   * PATCH version for backward compatible bug fixes

2. Update Changelog
   
   Add all notable changes under the new version number in ``CHANGELOG.md``

3. Create a Release
   
   Tag the release in git:

   .. code-block:: console

      $ git tag -a v1.0.0 -m "Release version 1.0.0"
      $ git push origin v1.0.0

Questions and Support
-------------------

* Open an issue on GitHub for bugs or feature requests
* Join our community discussions on GitHub Discussions
* Follow our Code of Conduct 