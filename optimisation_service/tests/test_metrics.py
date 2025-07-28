import numpy as np
import pytest

from app.internal.metrics import calculate_carbon_cost, calculate_payback_horizon


class TestCalculateCarbonCost:
    def test_good_inputs(self):
        res = calculate_carbon_cost(capex=10, carbon_balance_scope_1=10)
        assert res == 10 / (10 * 20 / 1000)

    @pytest.mark.parametrize("carbon_balance_scope_1", [0, -10])
    def test_null_and_negtative_carbon_balance_scope_1(self, carbon_balance_scope_1):
        res = calculate_carbon_cost(capex=10, carbon_balance_scope_1=carbon_balance_scope_1)
        assert res == float(np.finfo(np.float32).max)

    @pytest.mark.parametrize("capex", [0, -10])
    def test_null_and_negtative_capex(self, capex):
        res = calculate_carbon_cost(capex=capex, carbon_balance_scope_1=10)
        assert res == 0


class TestCalculateCalculatePaybackHorizon:
    def test_good_inputs(self):
        res = calculate_payback_horizon(capex=10, operating_balance=10)
        assert res == 10 / 10

    def test_negative_operating_balance(self):
        res = calculate_payback_horizon(capex=10, operating_balance=-10)
        assert res < 0

    def test_null_operating_balance(self):
        res = calculate_payback_horizon(capex=10, operating_balance=0)
        assert res < 0

    def test_null_vs_negative_operating_balance(self):
        res_null = calculate_payback_horizon(capex=10, operating_balance=0)
        res_neg = calculate_payback_horizon(capex=10, operating_balance=-10)
        assert res_null > res_neg

    @pytest.mark.parametrize("capex", [0, -10])
    def test_null_and_negtative_capex(self, capex):
        res = calculate_payback_horizon(capex=capex, operating_balance=10)
        assert res == 0
