import epoch_simulator as es

class TestTaskData:
    def test_can_hash_empties(self) -> None:
        td1 = es.TaskData()
        td2 = es.TaskData()

        assert td1 == td2

        assert hash(td1) == hash(td2)

    def test_can_hash_non_empty(self) -> None:
        td1 = es.TaskData()
        td1.building = es.Building()
        td1.building.scalar_heat_load = 1.0
        td2 = es.TaskData()
        td2.building = es.Building()
        td2.building.scalar_heat_load = 2.0
        assert td1 != td2
        assert hash(td1) != hash(td2)
