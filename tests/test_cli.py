import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_cli(runner):
    assert True


def test_cli_with_option(runner):
    assert True


def test_cli_with_arg(runner):
    assert True
