"""Test the properties of the electricity load synthesiser, mostly through daily_to_hh_eload."""

import datetime
import itertools
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import pytest

from app.dependencies import load_vae
from app.internal.elec_meters import daily_to_hh_eload
from app.internal.elec_meters.preprocessing import hh_to_square
from app.internal.elec_meters.vae import VAE
from app.internal.epl_typing import DailyDataFrame, HHDataFrame
from app.internal.gas_meters import parse_half_hourly


@pytest.fixture(scope="class")
def vae_model() -> VAE:
    """Load the VAE model."""
    return load_vae()


@pytest.fixture(scope="class")
def hh_df() -> HHDataFrame:
    """Get HH dataframe from a real site."""
    return parse_half_hourly("./tests/data/test_elec.csv").rename(columns={"consumption": "consumption_kwh"})


@pytest.fixture(scope="class")
def daily_df(hh_df: HHDataFrame) -> DailyDataFrame:
    """Resample HH dataframe into consistent days.."""
    new_df = hh_df.resample(pd.Timedelta(days=1)).sum(numeric_only=True)
    new_df["start_ts"] = new_df.index
    new_df["end_ts"] = new_df.index + pd.Timedelta(days=1)
    return cast(DailyDataFrame, new_df)


@pytest.fixture(scope="class")
def rng() -> np.random.Generator:
    """Get a repeatable RNG with an arbitrary seed."""
    return np.random.default_rng(seed=int(np.pi * 2**32))


def synthesised_eload_observed(
    vae_model: VAE, hh_df: HHDataFrame, daily_df: DailyDataFrame, rng: np.random.Generator
) -> HHDataFrame:
    """Get a synthetic eload from an observed HH dataframe."""
    square_df = hh_to_square(hh_df).ffill().bfill()
    return daily_to_hh_eload(daily_df=daily_df, model=vae_model, target_hh_observed_df=square_df, rng=rng)


def synthesised_eload_model_path(vae_model: VAE, daily_df: DailyDataFrame, rng: np.random.Generator) -> HHDataFrame:
    """Get a synthesised eload with the pretrained resids."""
    RESID_MODEL_PATH = Path(".", "models", "final", "arima")
    return daily_to_hh_eload(daily_df=daily_df, model=vae_model, resid_model_path=RESID_MODEL_PATH, rng=rng)


@pytest.fixture(scope="class")
def synthesised_eload(
    request: pytest.FixtureRequest, vae_model: VAE, hh_df: HHDataFrame, daily_df: DailyDataFrame, rng: np.random.Generator
) -> HHDataFrame:
    """Create a synthesised eload depending on the mode.

    This is a bit of indirection to allow pytest to use fixtures as parametrizations.
    """
    if request.param == "observed":
        return synthesised_eload_observed(vae_model=vae_model, hh_df=hh_df, daily_df=daily_df, rng=rng)

    if request.param == "model_path":
        return synthesised_eload_model_path(vae_model=vae_model, daily_df=daily_df, rng=rng)

    raise ValueError(f"Bad request param {request.param}")


@pytest.mark.parametrize("synthesised_eload", ["observed", "model_path"], indirect=True)
@pytest.mark.slow
class TestElecSynthStatistics:
    """Test the statistical properties of the electricity synthesiser."""

    def test_all_readings_positive(self, synthesised_eload: HHDataFrame) -> None:
        """Test that we are always consuming electricity."""
        is_negative_mask = synthesised_eload.consumption_kwh < 0
        assert (synthesised_eload.consumption_kwh >= 0).all(), f"Got negative readings: {synthesised_eload[is_negative_mask]}"

    def test_readings_non_zero(self, synthesised_eload: HHDataFrame) -> None:
        """Test that we consume at least some electricity."""
        assert synthesised_eload.consumption_kwh.sum() > 0, "Total usage was zero"

    def test_usage_every_day(self, synthesised_eload: HHDataFrame) -> None:
        """Test that we draw power every day."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        unique_days = sorted(set(synthesised_eload.index.date))
        for date in unique_days:
            in_day_mask = synthesised_eload.index.date == date
            in_day_df = synthesised_eload[in_day_mask]
            assert in_day_df["consumption_kwh"].sum() > 0, f"No usage on {date}"

    def test_midnights_similar(self, synthesised_eload: HHDataFrame) -> None:
        """Test that the jump from 23:30 to 00:30 is small."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        near_midnight_mask = np.logical_or(
            synthesised_eload.index.time == datetime.time(hour=23, minute=30),
            synthesised_eload.index.time == datetime.time(hour=0, minute=30),
        )
        near_midnight_df = synthesised_eload[near_midnight_mask]
        for i in range(0, len(near_midnight_df), 2):
            start, end = near_midnight_df["consumption_kwh"].iloc[i], near_midnight_df["consumption_kwh"].iloc[i + 1]
            THRESH = 0.1 * max(start, end)
            diff = np.abs(end - start)
            assert diff < THRESH, f"Difference between days {diff} greater than {THRESH}"

    def test_days_higher_mean(self, synthesised_eload: HHDataFrame) -> None:
        """Test that there is more usage during the day than at night."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        # Note that these masks don't overlap, so that we've got clearer day/night periods to compare
        is_day_mask = np.logical_and(synthesised_eload.index.hour >= 9, synthesised_eload.index.hour <= 17)
        is_night_mask = np.logical_or(synthesised_eload.index.hour <= 6, synthesised_eload.index.hour >= 20)
        # Make sure it's a bit bigger
        assert (
            synthesised_eload.loc[is_day_mask, "consumption_kwh"].mean()
            > synthesised_eload.loc[is_night_mask, "consumption_kwh"].mean() * 1.1
        )

    def test_days_higher_variance(self, synthesised_eload: HHDataFrame) -> None:
        """Test that the variance during the day is greater than the night variance."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        # Note that these masks don't overlap, so that we've got clearer day/night periods to compare
        is_day_mask = np.logical_and(synthesised_eload.index.hour >= 9, synthesised_eload.index.hour <= 17)
        is_night_mask = np.logical_or(synthesised_eload.index.hour <= 6, synthesised_eload.index.hour >= 20)
        # Make sure it's a bit bigger
        assert (
            cast(float, synthesised_eload.loc[is_day_mask, "consumption_kwh"].var(numeric_only=True))
            > cast(float, synthesised_eload.loc[is_night_mask, "consumption_kwh"].var(numeric_only=True)) * 1.1
        )

    def test_hh_readings_distinct(self, synthesised_eload: HHDataFrame) -> None:
        """
        Test that the half hourly readings each day are different.

        This checks that we haven't clipped too aggressively on the synthesised profile for this day.
        """
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        unique_days = sorted(set(synthesised_eload.index.date))
        for date in unique_days:
            in_day_mask = synthesised_eload.index.date == date
            in_day_df = synthesised_eload[in_day_mask]
            # forgive a few clashes
            unique_hhs = set(in_day_df["consumption_kwh"])
            assert len(unique_hhs) > 40, (
                f"Not enough unique entries on {date}, got {len(unique_hhs)}: {in_day_df['consumption_kwh'].to_numpy()}"
            )

    def test_mean_preserved(self, hh_df: HHDataFrame, synthesised_eload: HHDataFrame) -> None:
        """Test that the overall and daily means are preserved."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        assert isinstance(hh_df.index, pd.DatetimeIndex)
        expected_mean = hh_df["consumption_kwh"].mean()
        assert 0.8 * expected_mean <= synthesised_eload["consumption_kwh"].mean() <= 1.2 * expected_mean, (
            "Total mean outside of expected range"
        )

        bad_days_count = 0
        unique_days = sorted(set(synthesised_eload.index.date))
        for date in unique_days:
            synth_in_day_mask = synthesised_eload.index.date == date
            synth_in_day_df = synthesised_eload[synth_in_day_mask]

            hh_in_day_mask = hh_df.index.date == date
            hh_in_day_df = hh_df[hh_in_day_mask]

            if synth_in_day_df.empty or synth_in_day_df["consumption_kwh"].isna().any():
                print(f"Skipping {date} as empty or NaN synth")
                continue
            if hh_in_day_df.empty or hh_in_day_df["consumption_kwh"].isna().any():
                print(f"Skipping {date} as empty or NaN actuals")
                continue
            if len(hh_in_day_df) < 48:
                print(f"Skipping {date} as not complete HH data")
                continue

            expected_day_mean = hh_in_day_df["consumption_kwh"].mean()
            if not (0.5 * expected_day_mean <= synth_in_day_df["consumption_kwh"].mean() <= 1.5 * expected_day_mean):
                bad_days_count += 1
            # Permit some bad days but get a useful assert if we trip that
            if bad_days_count > 10:
                assert 0.5 * expected_day_mean <= synth_in_day_df["consumption_kwh"].mean() <= 1.5 * expected_day_mean, (
                    f"Bad mean on {date}, got synth={synth_in_day_df['consumption_kwh'].mean()} expected hh={expected_day_mean}"
                )

    def test_no_two_days_alike(self, synthesised_eload: HHDataFrame) -> None:
        """Test that all the days are different to one another."""
        assert isinstance(synthesised_eload.index, pd.DatetimeIndex)
        unique_days = sorted(set(synthesised_eload.index.date))

        for d1, d2 in itertools.combinations(unique_days, 2):
            if d1 == d2:
                continue
            in_d1_mask = synthesised_eload.index.date == d1
            in_d2_mask = synthesised_eload.index.date == d2
            in_d1_df = synthesised_eload[in_d1_mask]
            in_d2_df = synthesised_eload[in_d2_mask]
            assert not np.all(in_d1_df["consumption_kwh"].to_numpy() == in_d2_df["consumption_kwh"].to_numpy()), (
                f"{d1} readings same as {d2}"
            )


class TestObservedData:
    """Test that we can use funny bits of observed data."""

    def test_observed_from_other_year(
        self, vae_model: VAE, hh_df: HHDataFrame, daily_df: DailyDataFrame, rng: np.random.Generator
    ) -> None:
        """Test that we can use observed data from a different period."""
        square_df = hh_to_square(hh_df).ffill().bfill()
        square_df.index -= pd.Timedelta(days=365)
        # This should return okay
        new_df = daily_to_hh_eload(daily_df=daily_df, model=vae_model, target_hh_observed_df=square_df, rng=rng)
        assert isinstance(new_df, pd.DataFrame)

    def test_partial_observed(
        self, vae_model: VAE, hh_df: HHDataFrame, daily_df: DailyDataFrame, rng: np.random.Generator
    ) -> None:
        """Test that we can use partial observed data."""
        square_df = hh_to_square(hh_df).ffill().bfill()
        square_df = square_df[:90]
        # This should return okay
        new_df = daily_to_hh_eload(daily_df=daily_df, model=vae_model, target_hh_observed_df=square_df, rng=rng)
        assert isinstance(new_df, pd.DataFrame)
