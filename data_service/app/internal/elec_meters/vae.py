"""Model definition for a variational autoencoder for time series data."""

import torch
import torch.nn as nn


class VAE(nn.Module):  # noqa: D101
    def __init__(
        self, input_dim: int, aggregate_dim: int, date_dim: int, latent_dim: int, hidden_dim: int = 64, num_layers: int = 1
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
        """
        super().__init__()

        # LSTM Encoder for processing the time series data
        self.lstm_encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)

        # Fully connected layer to produce mean and log variance for the latent space
        self.encoder_fc = nn.Linear(hidden_dim * 2, latent_dim * 2)  # Combine LSTM output with non-temporal features

        # LSTM Decoder for generating the reconstructed time series
        self.lstm_decoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)

        # Fully connected layer for processing non-temporal features
        self.fc_non_temporal = nn.Sequential(nn.Linear(aggregate_dim + 2 * date_dim, hidden_dim), nn.ReLU())

        # Fully connected layer for initializing the LSTM hidden state
        self.fc_init_hidden = nn.Linear(latent_dim + hidden_dim, hidden_dim)

        # Fully connected layer to produce the final output (reconstructed time series)
        self.decoder_fc = nn.Linear(hidden_dim, input_dim)

        self.input_dim = input_dim  # save the input dimension for LSTM input initialization
        self.latent_dim = latent_dim  # save the latent dimension for extracting mu, log_var from output of self.encoder_fc()

    def encode(
        self, x: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Encode the input data into a latent space representation.

        Parameters
        ----------
        x (Tensor)
            Time series data.
        aggregate (Tensor)
            Aggregate values (non-temporal).
        start_date (Tensor)
            Start date of the period (non-temporal).
        end_date (Tensor)
            End date of the period (non-temporal).

        Returns
        -------
        Tensor: Mean (mu) and log variance (log_var) for the latent space.
        """
        # Process the time series data through the LSTM encoder
        _, (h_n, _) = self.lstm_encoder(x)  # h_n is the last hidden state from the LSTM
        h_n = h_n[-1]  # Take the hidden state from the last layer of the LSTM

        # Process the non-temporal features (aggregate, start date, end date) through fully connected layers
        non_temporal_input = torch.cat([aggregate, start_date, end_date], dim=1)
        non_temporal_features = self.fc_non_temporal(non_temporal_input)

        # Combine the LSTM output with the processed non-temporal features
        combined_features = torch.cat([h_n, non_temporal_features], dim=1)

        # Produce mean and log variance for the latent space
        h = self.encoder_fc(combined_features)
        mu, log_var = h[:, : self.latent_dim], h[:, self.latent_dim :]
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
    ) -> torch.Tensor:
        """
        Decode the latent vector into a reconstructed time series.

        Parameters
        ----------
        z (Tensor)
            Latent vector of shape (batch_size, latent_dim).
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (batch_size, 1).
        start_date (Tensor)
            Start date of the period (non-temporal) of shape (batch_size, 1).
        end_date (Tensor)
            End date of the period (non-temporal) of shape (batch_size, 1).
        seq_len (int)
            The length of the time series sequence (number of time steps).

        Returns
        -------
        Tensor: Reconstructed time series of shape (batch_size, seq_len, input_dim).
        """
        # Process the non-temporal features (aggregate, start date, end date)
        non_temporal_input = torch.cat([aggregate, start_date, end_date], dim=1)  # Shape: (batch_size, 3)
        processed_non_temporal = self.fc_non_temporal(non_temporal_input)  # Shape: (batch_size, hidden_dim)

        # Combine z with processed non-temporal features to form the context vector
        context_vector = torch.cat([z, processed_non_temporal], dim=1)  # Shape: (batch_size, latent_dim + hidden_dim)

        # lstm_input = self.fc_init_hidden(context_vector) # Shape: (batch_size, hidden_dim)
        # Initialize the LSTM hidden state using the context vector
        h_0 = self.fc_init_hidden(context_vector).unsqueeze(0)  # Shape: (1, batch_size, hidden_dim)
        c_0 = torch.zeros_like(h_0)  # Initialize the cell state as zeros

        # Initial input to the LSTM (typically a tensor of zeros)
        lstm_input = torch.zeros(context_vector.size(0), seq_len, self.input_dim).to(
            z.device
        )  # Shape: (batch_size, seq_len, input_dim)

        # Process through the LSTM decoder
        decoded_seq, _ = self.lstm_decoder(lstm_input, (h_0, c_0))  # Shape: (batch_size, seq_len, hidden_dim)
        # decoded_seq, _ = self.lstm_decoder(lstm_input)

        # Generate the final output using a fully connected layer
        output: torch.Tensor = self.decoder_fc(decoded_seq)  # Shape: (batch_size, seq_len, input_dim)
        return output

    def forward(
        self, x: torch.Tensor, aggregate: torch.Tensor, start_date: torch.Tensor, end_date: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass through the VAE: encode, reparameterize, and decode.

        Parameters
        ----------
        x (Tensor)
            Time series data of shape (batch_size, seq_len, input_dim).
        aggregate (Tensor)
            Aggregate values (non-temporal) of shape (batch_size, 1).
        start_date (Tensor)
            Start date of the period (non-temporal) of shape (batch_size, 1).
        end_date (Tensor)
            End date of the period (non-temporal) of shape (batch_size, 1).

        Returns
        -------
        Tensor: Reconstructed time series, mean (mu), and log variance (log_var).
        """
        # Input shape checking
        if len(x.shape) != 3 or x.shape[2] != 1:
            raise ValueError(f"Expected input 'x' to have shape (batch_size, seq_len, 1), but got {x.shape}")

        mu, log_var = self.encode(x, aggregate, start_date, end_date)
        z = self.reparameterize(mu, log_var)
        return self.decode(z, aggregate, start_date, end_date, x.shape[1]), mu, log_var
