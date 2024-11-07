import numpy as np

from app.internal.ga_utils import SimpleIntMutation


class TestSimpleIntMutation:
    def test_mut_simple_int_works(self):
        """
        Test mut_simple_int works with good inputs.
        """
        X = np.array([[1, 1], [2, 2], [0, 2]])
        xl = np.array([0, 0])
        xu = np.array([2, 2])
        prob = np.array([1, 0.5, 0])
        Xp = SimpleIntMutation.mut_simple_int(X, xl, xu, prob)
        assert np.min(Xp) >= 0
        assert np.max(Xp) <= 2
        assert not np.array_equal(X, Xp)
