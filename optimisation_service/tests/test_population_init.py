from app.internal.heuristics.population_init import generate_site_scenarios_from_heuristics
from app.models.core import Site


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
