"""pytest configuration for Clara AI integration tests."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: mark test as an integration test")


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:  # noqa: ANN001
    """Print a clean pass/fail summary block after the test run."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    errors = len(terminalreporter.stats.get("error", []))
    skipped = len(terminalreporter.stats.get("skipped", []))

    terminalreporter.write_sep("=", "CLARA AI INTEGRATION SUMMARY")
    terminalreporter.write_line(f"  PASSED  : {passed}")
    terminalreporter.write_line(f"  FAILED  : {failed + errors}")
    terminalreporter.write_line(f"  SKIPPED : {skipped}")
    terminalreporter.write_line(
        f"  RESULT  : {'✓ ALL CHECKS PASSED' if (failed + errors) == 0 else '✗ SOME CHECKS FAILED'}"
    )
    terminalreporter.write_sep("=", "")
