import runpy
import pytest
from unittest.mock import patch
from main import add


class TestAddBasic:
    def test_add_two_positive_numbers(self):
        assert add(1, 2) == 3

    def test_add_zero_and_positive(self):
        assert add(0, 5) == 5

    def test_add_positive_and_zero(self):
        assert add(7, 0) == 7

    def test_add_two_zeros(self):
        assert add(0, 0) == 0


class TestAddNegative:
    def test_add_two_negative_numbers(self):
        assert add(-3, -4) == -7

    def test_add_negative_and_positive(self):
        assert add(-10, 5) == -5

    def test_add_positive_and_negative(self):
        assert add(10, -3) == 7

    def test_add_negatives_that_cancel(self):
        assert add(-5, 5) == 0


class TestAddEdgeCases:
    def test_add_large_numbers(self):
        assert add(1_000_000, 2_000_000) == 3_000_000

    def test_add_large_negative_numbers(self):
        assert add(-1_000_000, -2_000_000) == -3_000_000

    def test_add_min_max_ints(self):
        result = add(-2**31, 2**31)
        assert result == 0

    def test_add_returns_int(self):
        result = add(2, 3)
        assert isinstance(result, int)


class TestMainEntrypoint:
    def test_main_runs_mcp_server(self):
        with patch("mcp.server.fastmcp.FastMCP.run") as mock_run:
            runpy.run_module("main", run_name="__main__")
            mock_run.assert_called_once_with(transport="sse")
