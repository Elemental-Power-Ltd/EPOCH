"""Model definition for a transformer-refined variational autoencoder for time series data."""

import numpy as np
import torch
from torch import nn


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer models."""

    def __init__(self, d_model: int, max_len: int = 5000) -> None:
        """
        Initialize positional encoding.

        Parameters
        ----------
        d_model (int)
            Dimension of the model
        max_len (int, optional)
            Maximum sequence length
        """
        super().__init__()

        # Create positional encoding matrix
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        # Register buffer (not a parameter, but part of the module)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding to input tensor.

        Parameters
        ----------
        x (Tensor)
            Time series data of shape (batch_size, seq_len, d_model).

        Returns
        -------
        Tensor with positional encoding added
        """
        x = x + self.pe[: x.size(1)]
        return x


class ResidualMLP(nn.Module):
    """A residual multi-layer perceptron (MLP) block."""

    def __init__(self, dim, hid_dim=None):
        super().__init__()
        hid_dim = hid_dim or dim
        self.net = nn.Sequential(
            nn.Linear(dim, hid_dim),
            nn.ReLU(),
            nn.Linear(hid_dim, dim),
        )

    def forward(self, x):
        """
        Forward pass through the residual MLP block.

        Args
        ----
            x (Tensor): Input tensor of shape [batch_size, dim].

        Returns
        -------
            Tensor: Output tensor of the same shape as input.
        """
        return x + self.net(x)


class VAE(nn.Module):  # noqa: D101
    def __init__(
        self,
        input_dim: int,
        aggregate_dim: int,
        date_dim: int,
        latent_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 1,
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
        hidden_dim (int, optional)
            The dimensionality of the hidden states in the LSTM layers (default is 64).
        num_layers (int, optional)
            The number of layers in the LSTM (default is 1).
        dropout_decoder (float, optional)
            Dropout probability for decoder module; if None, dropout not implemented
        """
        super().__init__()

        # LSTM Encoder for processing the time series data
        self.lstm_encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.residual_mlp_block = ResidualMLP(dim=hidden_dim, hid_dim=2 * hidden_dim)

        # Fully connected layer to produce mean and log variance for the latent space
        self.encoder_fc = nn.Sequential(nn.Linear(hidden_dim + 1, latent_dim * 2), nn.ReLU())
        # Combine LSTM output with non-temporal features
        # input here will be concatenated output of self.lstm_encoder() and aggregate
        # use ReLU as activation functions -- output will be the mean / variance of the latent space

        # LSTM Decoder for generating the reconstructed time series
        self.lstm_decoder = nn.LSTM(latent_dim + 2, hidden_dim, num_layers, batch_first=True)

        # Fully connected layers for initialising the LSTM hidden state, cell state and input sequence
        # Use LeakyReLU as activation function here -- more robust version of ReLU (fewer dead)
        self.fc_init_hidden = nn.Sequential(nn.Linear(latent_dim + 1, hidden_dim), nn.LeakyReLU())
        self.fc_init_cell = nn.Sequential(nn.Linear(latent_dim + 1, hidden_dim), nn.LeakyReLU())

        # Dropout layer for the decoder, to mitigate against posterior collapse
        if dropout_decoder is not None:
            self.dropout_layer = nn.Dropout(dropout_decoder)

        # Fully connected layer to produce the final output (reconstructed time series)
        self.decoder_fc_mu = nn.Sequential(nn.Linear(hidden_dim, input_dim), nn.LeakyReLU())
        self.decoder_fc_logvar = nn.Sequential(nn.Linear(hidden_dim, input_dim), nn.LeakyReLU())

        self.input_dim = input_dim  # save the input dimension for LSTM input initialization
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.latent_dim = latent_dim  # save the latent dimension for extracting mu, log_var from output of self.encoder_fc()
        self.dropout_decoder_flag = dropout_decoder is not None  # whether we're using dropout in the decoder module

    def encode(
        self, x: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Encode the input data into a latent space representation.

        Parameters
        ----------
        x (Tensor)
            Time series data of shape [batch_size, n_days, 48, input_dim]
        aggregate (Tensor)
            Aggregate values (non-temporal); tensor of shape [batch_size, n_days, 1]
        start_date (Tensor)
            Start date of the period (non-temporal); tensor of shape [batch_size, n_days, 1]
        end_date (Tensor)
            End date of the period (non-temporal); tensor of shape [batch_size, n_days, 1]

        Returns
        -------
        Tensors: Mean (mu) and log variance (log_var) for the latent space. Each has dimension [batch_size, n_days, latent_dim]
        """
        batch_size, n_days, seq_len, _ = x.shape
        # Reshape inputs for VAE encoder to treat each day independently
        x = x.reshape(batch_size * n_days, seq_len, -1)
        aggregate = aggregate.reshape(batch_size * n_days, -1)
        # start_date = start_date.reshape(batch_size * n_days, -1)
        # end_date = end_date.reshape(batch_size * n_days, -1)

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

    def decode(
        self, z: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor, seq_len: int
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Decode the latent vector into a reconstructed time series.

        Parameters
        ----------
        z (Tensor)
            Latent vector of shape (batch_size, n_days, latent_dim).
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (batch_size, n_days, 1).
        start_date (Tensor)
            Start date of the period (non-temporal) of shape (batch_size, n_days, 1).
        end_date (Tensor)
            End date of the period (non-temporal) of shape (batch_size, n_days, 1).
        seq_len (int)
            The length of the time series sequence (number of time steps).

        Returns
        -------
        Tensors: Mean (mu) and log variance (log_var) at each time step for the reconstructed time series.
            Each has dimension [batch_size, n_days, latent_dim]
        """
        batch_size, n_days, _ = z.shape

        # Reshape inputs for VAE decoder to treat each day independently
        z = z.reshape(batch_size * n_days, -1)
        aggregate = aggregate.reshape(batch_size * n_days, -1)

        # Combine z with the aggregate to form the context vector
        context_vector = torch.cat([z, aggregate], dim=1)
        # Shape: (batch_size * n_days, latent_dim + 1)

        # h0 and c0 should be projected versions of both the latent and the conditioning variable
        # input to the lstm should be tiled latent concatenated with conditioning variables
        # Initialize the LSTM hidden state and cell state using the context vector
        h_0 = (
            self.fc_init_hidden(context_vector).unsqueeze(0).repeat(self.num_layers, 1, 1)
        )  # Shape: (num_layers, batch_size * n_days, hidden_dim)
        c_0 = (
            self.fc_init_cell(context_vector).unsqueeze(0).repeat(self.num_layers, 1, 1)
        )  # Shape: (num_layers, batch_size * n_days, hidden_dim)

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

        # If dropout parameter activated, apply dropout to the LSTM input sequence
        # dropout for h0,c0 introduces randomness at the core of the sequence dynamics, which can destabilize training
        if self.dropout_decoder_flag:
            lstm_input = self.dropout_layer(lstm_input)

        # Process through the LSTM decoder
        decoded_seq, _ = self.lstm_decoder(lstm_input, (h_0, c_0))  # Shape: (batch_size * n_days, seq_len, hidden_dim)

        # Generate the final output using a fully connected nnet
        output_mu = self.decoder_fc_mu(decoded_seq)  # Shape: (batch_size * n_days, seq_len, input_dim)
        output_logvar = self.decoder_fc_logvar(decoded_seq)  # Shape: (batch_size * n_days, seq_len, input_dim)

        # Reshape outputs to correspond to input dimensions
        output_mu = output_mu.reshape(batch_size, n_days, seq_len, -1)  # Shape: (batch_size, n_days, seq_len, input_dim, 2)
        output_logvar = output_logvar.reshape(
            batch_size, n_days, seq_len, -1
        )  # Shape: (batch_size, n_days, seq_len, input_dim, 2)
        return output_mu, output_logvar

    def forward(
        self, x: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor
    ) -> dict[str, torch.Tensor]:
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
        mu, log_var = self.encode(x, aggregate, start_date, end_date)
        z = self.reparameterize(mu, log_var)
        out_mu, out_logvar = self.decode(z, aggregate, start_date, end_date, x.shape[2])

        return {"reconstructed": torch.cat([out_mu, out_logvar], dim=-1), "mu": mu, "logvar": log_var}


class TransformerRefinement(nn.Module):
    """Transformer module for refining hi-res predictions."""

    def __init__(self, d_model: int, nhead: int, num_layers: int, dim_feedforward: int, dropout: float = 0.1) -> None:
        """
        Initialize transformer refinement module.

        Parameters
        ----------
        d_model (int)
            Dimension of the model
        nhead (int)
            Number of attention heads
        num_layers (int)
            Number of transformer layers
        dim_feedforward (int)
            Dimension of feedforward network
        dropout (float, optional)
            Dropout probability
        """
        super().__init__()

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model)

        # Transformer encoder layers
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """
        Forward pass through transformer.

        Parameters
        ----------
        x (Tensor)
            Input tensor of shape [batch_size * n_days, seq_len, d_model]
        mask (Tensor, optional)
            Optional mask for transformer

        Returns
        -------
            Refined tensor of shape [batch_size * n_days, seq_len, d_model]
        """
        # Add positional encoding
        x = self.pos_encoder(x)

        # Apply transformer
        output = self.transformer_encoder(x, mask=mask)

        return output


class TransformerVAE(nn.Module):
    """
    Complete model for time series upsampling using a conventional VAE followed by a transformer.

    This model takes hh data as input, compresses it to a lower-resolution time series using an LSTM,
    combines this lo-res time series with non-temporal features (e.g. daily aggs) to obtain a latent
    space representation, reconstructs the hh data, and refines this construction with a transformer
    """

    def __init__(
        self,
        input_dim: int,
        aggregate_dim: int,
        date_dim: int,
        latent_dim: int,
        transformer_dim: int,
        nhead: int,
        transformer_layers: int,
        hidden_dim: int = 64,
        num_layers: int = 1,
        dropout_vae: float | None = None,
        dropout_transformer: float = 0.1,
    ) -> None:
        """
        Initialize the model.

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
        transformer_dim (int)
            The dimensionality of the transformer model
        nhead (int)
            Number of attention heads in transformer
        transformer_layers (int)
            Number of transformer layers
        hidden_dim (int, optional)
            The dimensionality of the hidden states in the LSTM layers (default is 64).
        num_layers (int, optional)
            The number of layers in the LSTM (default is 1).
        dropout_vae (float or None, optional)
            Dropout probability for VAE decoder; if None, then dropout not implemented
        dropout_transformer (float, optional)
            Dropout probability for transformer
        """
        super().__init__()

        # VAE for initial hh predictions
        self.vae = VAE(input_dim, aggregate_dim, date_dim, latent_dim, hidden_dim, num_layers, dropout_vae)

        # Projection from VAE output to transformer dimension if needed
        if input_dim != transformer_dim:
            self.projection = nn.Linear(input_dim, transformer_dim)
        else:
            self.projection = nn.Identity()

        # Transformer for temporal refinement
        self.transformer = TransformerRefinement(
            d_model=transformer_dim,
            nhead=nhead,
            num_layers=transformer_layers,
            dim_feedforward=transformer_dim * 4,
            dropout=dropout_transformer,
        )

        # Projection from transformer dimension back to input dimension if needed
        if transformer_dim != input_dim:
            self.output_projection = nn.Linear(transformer_dim, input_dim)
        else:
            self.output_projection = nn.Identity()

        self.input_dim = input_dim  # save the input dimension for LSTM input initialization
        self.latent_dim = latent_dim  # save the latent dimension for extracting mu, log_var from output of self.encoder_fc()
        self.transformer_dim = transformer_dim

    def forward(
        self, x: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass through the model: VAE, transformer.

        Args:
            x (Tensor)
                Hi-res data tensor of shape [batch_size, n_days, 48, features]
            aggregate (Tensor)
                Aggregate values (non-temporal) of shape [batch_size, n_days, 1].
            start_date (Tensor)
                Start date of the period (non-temporal) of shape [batch_size, n_days, date_dim].
            end_date (Tensor)
                End date of the period (non-temporal) of shape [batch_size, n_days, date_dim].

        Returns
        -------
            Dictionary containing model outputs
        """
        # Input shape checking
        if len(x.shape) != 4 or x.shape[3] != 1:
            raise ValueError(f"Expected input 'x' to have shape (batch_size, n_days, 48, 1), but got {x.shape}")

        batch_size, n_days, seq_len, _ = x.shape

        # if np.isnan(x.detach()).any() or np.isnan(aggregate.detach()).any():
        #     print(f"are there nans in x input? {np.isnan(x.detach()).any()}")
        #     print(f"are there nans in aggregate input? {np.isnan(aggregate.detach()).any()}")
        #     raise ValueError("nans experienced in TransformerVAE before calling self.vae")

        # Pass through VAE
        vae_output = self.vae(x, aggregate, start_date, end_date)
        hh_reconstructed_dists = vae_output["reconstructed"]
        hh_reconstructed = hh_reconstructed_dists[:, :, :, :1]  # use means of returned distributions

        # Project to transformer dimension
        projected = self.projection(hh_reconstructed)  # projection nnet operates on last dimension

        # Reshape for transformer - keep the same batch size, but concatenate overlapping days
        projected_overlap = torch.cat([projected[:, :-1, :, :], projected[:, 1:, :, :]], dim=2)
        # Shape: (batch_size, n_days-1, seq_len*2, transformer_dim)

        # Combine batch and overlapped day dimensions
        transformer_input = projected_overlap.reshape(batch_size * (n_days - 1), seq_len * 2, -1)

        # Apply transformer
        transformer_output = self.transformer(transformer_input)

        # Reshape back
        refined_overlap = transformer_output.reshape(batch_size, n_days - 1, seq_len * 2, -1)
        refined = torch.cat([refined_overlap[:, :, :seq_len, :], refined_overlap[:, -1:, seq_len:, :]], dim=1)

        # Project back to input dimension if needed
        refined = self.output_projection(refined)
        # Shape: (batch_size, n_days, seq_len, input_dim)

        return {
            "hh_predictions": refined,
            "vae_reconstructed_mu": hh_reconstructed[:, :, :, :1],
            "vae_reconstructed_logvar": hh_reconstructed_dists[:, :, :, 1:],
            "mu": vae_output["mu"],
            "logvar": vae_output["logvar"],
        }

    def generate(
        self, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor, seq_len: int = 48
    ) -> torch.Tensor:
        """
        Generate hh predictions from daily data.

        Parameters
        ----------
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (n_days, 1).
        start_date (Tensor)
            Start date of the period (non-temporal) of shape (n_days, 1).
        end_date (Tensor)
            End date of the period (non-temporal) of shape (n_days, 1).
        seq_len (int)
            The length of the time series sequence (number of time steps).


        Returns
        -------
        Tensor: Reconstructed time series of shape (batch_size=1, seq_len, input_dim).
        """
        n_days, features = aggregate.shape
        device = next(self.parameters()).device

        # for .generate(), batch_size will be 1 by default
        # for VAE part, reshape and generate all
        # Create latent vectors by sampling from a standard Gaussian distn
        z = torch.randn(n_days, self.vae.latent_dim, device=device)

        # Reshape for batch processing
        z_batch = z.reshape(1, n_days, self.vae.latent_dim)

        # Decode to get half-hourly predictions
        hh_batch = self.vae.decode(z_batch, aggregate, start_date, end_date, seq_len)
        # Shape: (batch_size, n_days, seq_len, features)

        # Project to transformer dimension
        projected = self.projection(hh_batch)  # projection nnet operates on last dimension

        # Reshape for transformer - keep the same batch size, but concatenate overlapping days
        projected_overlap = torch.cat([projected[:, :-1, :, :], projected[:, 1:, :, :]], dim=2)
        # Shape: (batch_size, n_days-1, seq_len*2, features)

        # Combine batch and overlapped day dimensions
        transformer_input = projected_overlap.reshape(1 * (n_days - 1), seq_len * 2, -1)

        # Apply transformer
        transformer_output = self.transformer(transformer_input)

        # Reshape back
        refined_overlap = transformer_output.reshape(1, n_days - 1, seq_len * 2, -1)
        refined = torch.cat([refined_overlap[:, :, :seq_len, :], refined_overlap[:, -1:, seq_len:, :]], dim=1)
        # Shape: (1, n_days, seq_len, transformer_dim)

        # Project back and reshape to final output
        refined = self.output_projection(refined)  # projection nnet operates on last dimension
        refined = refined.reshape(n_days, seq_len, features)

        return refined
