import unittest

import numpy as np
import pandas as pd

from src.forecast import fit_models, time_years


class ForecastTests(unittest.TestCase):
    def test_time_years(self):
        dates = pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"]))
        values = time_years(dates, pd.Timestamp("2020-01-01"))
        self.assertAlmostEqual(values[0], 0.0)
        self.assertTrue(0.99 < values[1] < 1.01)

    def test_power_model_returns_finite_forecast(self):
        frame = pd.DataFrame({
            "observed_date": pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"]),
            "total_citations": [80, 150, 230, 320],
        })
        models = fit_models(frame, pd.Timestamp("2020-01-01"))
        future = models["power"].predict(np.array([4.0]))
        self.assertTrue(np.isfinite(future[0]))
        self.assertGreater(future[0], 0)


if __name__ == "__main__":
    unittest.main()
