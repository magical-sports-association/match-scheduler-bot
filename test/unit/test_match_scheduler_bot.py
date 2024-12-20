"""Tests for match_scheduler_bot"""

import pytest

import match_scheduler_bot

def test_vacuous():
    """A test that passes vacuously"""
    pass

def test_exception():
    """A test that checks if an exception was raised"""
    with pytest.raises(ValueError):
        raise ValueError()

@pytest.mark.parametrize("x, y", [(a, b) for a in range(10) for b in range(10)])
def test_parametrize(x, y):
    """Test cases can be parametrized to test multiple inputs at once"""
    assert x + y == y + x
