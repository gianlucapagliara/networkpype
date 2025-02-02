"""Test suite for the NetworkPype package.

This package contains comprehensive tests for all components of NetworkPype,
including unit tests, integration tests, and fixtures. The tests are organized
by component and use pytest as the testing framework.

Test Organization:
    - test_rest/: Tests for REST client functionality
    - test_websocket/: Tests for WebSocket client functionality
    - test_throttler/: Tests for rate limiting functionality
    - conftest.py: Shared pytest fixtures and configuration
    - utils.py: Test utilities and helper functions

Running Tests:
    The tests can be run using pytest:
    ```bash
    # Run all tests
    pytest

    # Run tests for a specific component
    pytest tests/test_rest/

    # Run tests with coverage
    pytest --cov=networkpype

    # Run tests and generate HTML coverage report
    pytest --cov=networkpype --cov-report=html
    ```

Writing Tests:
    When adding new tests:
    1. Place them in the appropriate component directory
    2. Use the provided fixtures from conftest.py
    3. Follow the existing test style and naming conventions
    4. Include both positive and negative test cases
    5. Add docstrings explaining test purpose and methodology
"""
