"""Tests for the VAE without the usual endpoint scaffolding."""

# ruff: noqa: D101

import datetime

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler  # type: ignore

from app.dependencies import load_vae
from app.internal.elec_meters.model_utils import ScalerTypeEnum, load_all_scalers
from app.internal.elec_meters.vae import VAE


class TestVAE:
    def test_untrained(self) -> None:
        """Test that we can use an untrained model with the right shapes."""
        model = VAE(input_dim=1, latent_dim=5)

        scalers = {
            ScalerTypeEnum.Aggregate: StandardScaler().fit(np.array([0.0, 10000]).reshape(-1, 1)),
            ScalerTypeEnum.Data: StandardScaler().fit(np.array([0.0, 10000]).reshape(-1, 1)),
        }

        daily_df = pd.DataFrame(
            {
                "start_ts": [datetime.datetime(year=2024, month=1, day=i, tzinfo=datetime.UTC) for i in range(1, 30)],
                "end_ts": [datetime.datetime(year=2024, month=1, day=i, tzinfo=datetime.UTC) for i in range(1, 30)],
                "consumption_kwh": 10000 * np.random.default_rng().random(size=29),
            }
        )
        with torch.no_grad():
            consumption_scaled = torch.from_numpy(
                scalers[ScalerTypeEnum.Aggregate]
                .transform(daily_df["consumption_kwh"].to_numpy().reshape(-1, 1))
                .astype(np.float32)
            )
            zs = torch.randn(size=[1, daily_df.shape[0], model.latent_dim], dtype=torch.float32)
            result_scaled = model.decode(zs, consumption_scaled, seq_len=48).squeeze().detach().numpy()
            assert result_scaled.shape == (29, 48)

    def test_trained(self) -> None:
        """Test that we can use a pre-baked trained model with random data."""
        elec_vae_mdl = load_vae()
        scalers = load_all_scalers()

        daily_df = pd.DataFrame(
            {
                "start_ts": [datetime.datetime(year=2024, month=1, day=i, tzinfo=datetime.UTC) for i in range(1, 30)],
                "end_ts": [datetime.datetime(year=2024, month=1, day=i, tzinfo=datetime.UTC) for i in range(1, 30)],
                "consumption_kwh": 10000 * np.random.default_rng().random(size=29),
            }
        )
        with torch.no_grad():
            consumption_scaled = torch.from_numpy(
                scalers[ScalerTypeEnum.Aggregate]
                .transform(daily_df["consumption_kwh"].to_numpy().reshape(-1, 1))
                .astype(np.float32)
            )
            # Batch size, n days, latent dim
            zs = torch.randn(size=[1, daily_df.shape[0], elec_vae_mdl.latent_dim], dtype=torch.float32)
            result_scaled = elec_vae_mdl.decode(zs, consumption_scaled, seq_len=48).squeeze().detach().numpy()
            # result = scalers[ScalerTypeEnum.Data].inverse_transform(result_scaled.squeeze().detach().numpy())
            assert result_scaled.shape == (29, 48)
