"""Model definition for a variational autoencoder for time series data."""

from typing import cast

import numpy as np
import torch
from torch import nn


class ResidualMLP(nn.Module):
    """A residual multi-layer perceptron (MLP) block with two layers."""

    def __init__(self, dim: int, hid_dim: int | None = None):
        """
        Initialise the ResidualMLP class.

        Parameters
        ----------
        dim (int)
            Input dimension of the first layer, output dimension of the second layer.
        hid_dim (int, optional)
            Output dimension of the first layer, input dimension of the second layer.
            If not provided, dim is used instead.
        """
        super().__init__()
        hid_dim = hid_dim or dim
        self.net = nn.Sequential(
            nn.Linear(dim, hid_dim),
            nn.ReLU(),
            nn.Linear(hid_dim, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the residual MLP block.

        Args
        ----
            x (Tensor): Input tensor of shape [batch_size, dim].

        Returns
        -------
            Tensor: Output tensor of the same shape as input.
        """
        return cast(torch.Tensor, x + self.net(x))


class VAE(nn.Module):  # noqa: D101
    def __init__(
        self,
        input_dim: int,
        latent_dim: int,
        hidden_dim_encoder: int = 64,
        hidden_dim_decoder: int = 64,
        num_layers_encoder: int = 1,
        num_layers_decoder: int = 1,
        dropout_decoder: float | None = None,
    ) -> None:
        """
        Initialise the VAE Class.

        Parameters
        ----------
        input_dim (int)
            The dimensionality of the time series data (i.e. the no of features per time step).
            For elec smart meter data, this will usually be 1.
        aggregate_dim (int)
            The dimensionality of the aggregate value input (typically 1).
        date_dim (int)
            The dimensionality of the date input (e.g., start and end dates, typically 1 each).
        latent_dim (int)
            The dimensionality of the latent space (i.e., the size of the compressed representation).
        hidden_dim_encoder, hidden_dim_decoder (int, optional)
            The dimensionality of the hidden states in the LSTM layers (default is 64).
        num_layers_encoder, num_layers_decoder (int, optional)
            The number of layers in the LSTM (default is 1).
        dropout_decoder (float, optional)
            Dropout probability for decoder module; if None, dropout not implemented
        """
        super().__init__()

        # LSTM Encoder for processing the time series data
        self.lstm_encoder = nn.LSTM(input_dim, hidden_dim_encoder, num_layers_encoder, batch_first=True)

        # Residual FC block for increasing depth of encoder
        self.residual_mlp_block = ResidualMLP(dim=hidden_dim_encoder, hid_dim=2 * hidden_dim_encoder)

        # Fully connected layer to produce mean and log variance for the latent space
        self.encoder_fc = nn.Sequential(nn.Linear(hidden_dim_encoder + 1, latent_dim * 2), nn.ReLU())
        # Combine LSTM output with non-temporal features
        # input here will be concatenated output of self.lstm_encoder() and aggregate
        # use ReLU as activation functions -- output will be the mean / variance of the latent space

        # LSTM Decoder for generating the reconstructed time series
        self.lstm_decoder = nn.LSTM(latent_dim + 2, hidden_dim_decoder, num_layers_decoder, batch_first=True)

        # Fully connected layers for initialising the LSTM hidden state, cell state and input sequence
        # Use LeakyReLU as activation function here -- more robust version of ReLU (fewer dead)
        self.fc_init_hidden = nn.Sequential(nn.Linear(latent_dim + 1, hidden_dim_decoder), nn.LeakyReLU())
        self.fc_init_cell = nn.Sequential(nn.Linear(latent_dim + 1, hidden_dim_decoder), nn.LeakyReLU())

        # Dropout layer for the decoder, to mitigate against posterior collapse
        if dropout_decoder is not None:
            self.dropout_layer = nn.Dropout(dropout_decoder)

        # Fully connected layer to produce the final output (reconstructed time series)
        self.decoder_fc = nn.Sequential(nn.Linear(hidden_dim_decoder, input_dim), nn.LeakyReLU())  # no final activation

        self.latent_dim = latent_dim  # save the latent dimension for extracting mu, log_var from output of self.encoder_fc()
        self.dropout_decoder_flag = dropout_decoder is not None  # whether we're using dropout in the decoder module

    def encode(
        self,
        x: torch.Tensor,
        aggregate: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Encode the input data into a latent space representation.

        Parameters
        ----------
        x (Tensor)
            Time series data of shape [batch_size, n_days, 48, input_dim]
        aggregate (Tensor)
            Aggregate values (non-temporal); tensor of shape [batch_size, n_days, 1]

        Returns
        -------
        Tensors: Mean (mu) and log variance (log_var) for the latent space. Each has dimension [batch_size, n_days, latent_dim]
        """
        batch_size, n_days, seq_len, _ = x.shape
        # Reshape inputs for VAE encoder to treat each day independently
        x = x.reshape(batch_size * n_days, seq_len, -1)
        aggregate = aggregate.reshape(batch_size * n_days, -1)

        # Process the time series data through the LSTM encoder
        _, (h_n, _) = self.lstm_encoder(x)  # h_n is the last hidden state from the LSTM
        h_n = h_n[-1]  # Take the hidden state from the last layer of the LSTM

        # Pass through a residual MLP block to increase depth and expressiveness of encoder
        h_n = self.residual_mlp_block(h_n)

        # Combine the LSTM output with the aggregate
        combined_features = torch.cat([h_n, aggregate], dim=1)

        # Produce mean and log variance for the latent space
        h = self.encoder_fc(combined_features)
        mu, log_var = h[:, : self.latent_dim], h[:, self.latent_dim :]

        # Reshape outputs to correspond to input dimensions
        mu = mu.reshape(batch_size, n_days, -1)
        log_var = log_var.reshape(batch_size, n_days, -1)

        return mu, log_var

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        """
        Reparameterize the latent space using the reparameterization trick.

        Parameters
        ----------
        mu (Tensor)
            Mean of the latent space distribution.
        log_var (Tensor)
            Log variance of the latent space distribution.

        Returns
        -------
            Tensor: A sampled latent vector z.
        """
        std = torch.exp(0.5 * log_var)  # Calculate the standard deviation
        eps = torch.randn_like(std)  # Sample from a standard normal distribution
        return mu + eps * std  # Reparameterization trick

    def decode(self, z: torch.Tensor, aggregate: torch.Tensor, seq_len: int) -> torch.Tensor:
        """
        Decode the latent vector into a reconstructed time series.

        Parameters
        ----------
        z (Tensor)
            Latent vector of shape (batch_size, n_days, latent_dim).
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (batch_size, n_days, 1).
        seq_len (int)
            The length of the time series sequence (number of time steps).

        Returns
        -------
        Tensor: Reconstructed time series of shape (batch_size, n_days, seq_len, input_dim).
        """
        batch_size, n_days, latent_dim = z.shape
        assert latent_dim == self.latent_dim, f"Wrong latent dimension in {z.shape} (should be last dimension)"
        # Reshape inputs for VAE decoder to treat each day independently
        z = z.reshape(batch_size * n_days, -1)
        aggregate = aggregate.reshape(batch_size * n_days, -1)

        # Combine z with the aggregate to form the context vector
        context_vector = torch.cat([z, aggregate], dim=1)
        # Shape: (batch_size * n_days, latent_dim + 1)

        # Initialize the LSTM hidden state and cell state using the context vector
        # h0 and c0 should be projected versions of both the latent and the conditioning variable
        # input to the lstm should be tiled latent concatenated with the conditioning variable
        h_0 = self.fc_init_hidden(context_vector).unsqueeze(0)  # Shape: (1, batch_size * n_days, hidden_dim)
        c_0 = self.fc_init_cell(context_vector).unsqueeze(0)  # Shape: (1, batch_size * n_days, hidden_dim)

        # Initial input to the LSTM (tiled context vector)
        lstm_input = context_vector.unsqueeze(1).repeat(1, seq_len, 1)
        # Shape: (batch_size * n_days, seq_len, latent_dim + 1)

        # Concatenate time step embedding to each input iteration
        lstm_input = torch.cat(
            [
                lstm_input,
                torch.Tensor(np.arange(1, seq_len + 1, dtype=np.float64) / seq_len)
                .unsqueeze(0)
                .unsqueeze(2)  # Shape: (1, seq_len, 1)
                .expand(lstm_input.shape[0], -1, -1)  # Shape: (batch_size * n_days, seq_len, 1)
                .to(z.device),
            ],
            dim=2,
        )  # Shape: (batch_size * n_days, seq_len, latent_dim + 2)

        # If dropout parameter activated, apply dropout to (only) the LSTM input sequence
        # dropout for h0,c0 introduces randomness at the core of the sequence dynamics, which can destabilize training
        if self.dropout_decoder_flag:
            lstm_input = self.dropout_layer(lstm_input)

        # Process through the LSTM decoder
        decoded_seq, _ = self.lstm_decoder(lstm_input, (h_0, c_0))  # Shape: (batch_size * n_days, seq_len, hidden_dim)

        # Generate the final output using a fully connected nnet
        output = self.decoder_fc(decoded_seq)  # Shape: (batch_size * n_days, seq_len, input_dim)

        # Reshape outputs to correspond to input dimensions
        output = output.reshape(batch_size, n_days, seq_len, -1)  # Shape: (batch_size, n_days, seq_len, input_dim)
        return cast(torch.Tensor, output)

    def forward(self, x: torch.Tensor, aggregate: torch.Tensor) -> dict[str, torch.Tensor]:
        """
        Forward pass through the VAE: encode, reparameterize, and decode.

        Parameters
        ----------
        x (Tensor)
            Time series data of shape (batch_size, n_days, seq_len, input_dim).
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (batch_size, n_days, 1).
        start_date (Tensor)
            Start date of the period (non-temporal) of shape (batch_size, n_days, 1).
        end_date (Tensor)
            End date of the period (non-temporal) of shape (batch_size, n_days, 1).

        Returns
        -------
        Tensor: Reconstructed time series, mean (mu), and log variance (log_var).
        """
        # Input shape checking
        if len(x.shape) != 4 or x.shape[3] != 1:
            raise ValueError(f"Expected input 'x' to have shape (batch_size, n_days, seq_len, 1), but got {x.shape}")
        mu, log_var = self.encode(x, aggregate)
        z = self.reparameterize(mu, log_var)

        return {"reconstructed": self.decode(z, aggregate, x.shape[2]), "mu": mu, "logvar": log_var}
