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
        res = calculate_payback_horizon(capex=10, cost_balance=10)
        assert res == 10 / 10

    @pytest.mark.parametrize("cost_balance", [0, -10])
    def test_null_and_negtative_cost_balance(self, cost_balance):
        res = calculate_payback_horizon(capex=10, cost_balance=cost_balance)
        assert res == float(np.finfo(np.float32).max)

    @pytest.mark.parametrize("capex", [0, -10])
    def test_null_and_negtative_capex(self, capex):
        res = calculate_payback_horizon(capex=capex, cost_balance=10)
        assert res == 0
