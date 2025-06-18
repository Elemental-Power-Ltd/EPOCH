from app.internal.heuristics.asset_heuristics import get_all_estimates
from app.internal.heuristics.population_init import (
    generate_asset_from_heuristics,
    generate_site_scenarios_from_heuristics,
    normal_choice,
)
from app.models.core import Site
from app.models.epoch_types.site_range_type import HeatPump, HeatSourceEnum


class TestGenerateSiteScenariosFromHeuristics:
    def test_good_inputs(self, default_site: Site):
        epoch_data = default_site._epoch_data
        site_range = default_site.site_range
        pop_size = 2
        res = generate_site_scenarios_from_heuristics(site_range=site_range, epoch_data=epoch_data, pop_size=pop_size)

        assert len(res) == pop_size
        for individual in res:
            assert hasattr(individual, "building")
            assert hasattr(individual, "config")
            assert hasattr(individual, "grid")

    def test_generate_asset(self, default_site: Site):
        estimates = get_all_estimates(default_site._epoch_data)

        power_options = [50.0, 75.0]

        heat_pump_range = HeatPump(
            COMPONENT_IS_MANDATORY=False,
            heat_power=power_options,
            heat_source=[HeatSourceEnum.AMBIENT_AIR],
            send_temp=[65],
            incumbent=False,
            age=0,
            lifetime=10
        )

        asset = generate_asset_from_heuristics("heat_pump", heat_pump_range.model_dump(), estimates)

        assert asset["heat_power"] in power_options


class TestNormalChoice:
    def test_good_inputs(self):
        choices = [25, 50, 75]
        estimate = choices[0]
        res = normal_choice(estimate, choices, 0.1)
        assert res in choices

    def test_large_estimate(self):
        choices = [25, 50, 75]
        estimate = max(choices) * 10
        res = normal_choice(estimate, choices, 0.1)
        assert res == max(choices)

    def test_small_estimate(self):
        choices = [25, 50, 75]
        estimate = min(choices) / 10
        res = normal_choice(estimate, choices, 0.1)
        assert res == min(choices)
