"""
Training module for time series upsampling.

This module implements training functions for the VAE model in vae_2_0.py.
"""

import logging
import warnings
from collections.abc import Collection
from pathlib import Path
from typing import TypedDict, cast

import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.figure import Figure
from torch import nn, optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from torch.utils.tensorboard.writer import SummaryWriter

from app.internal.elec_meters.vae_2_0 import VAE

logger = logging.getLogger(__name__)

class LossesComponentsDict(TypedDict):  # noqa: D101
    recon: float
    kl: float
    temporal: float


class LossesDict(TypedDict):
    """
    Custom type for the output the train_epoch() and validate() functions below.

    Attributes
    ----------
    loss (float):
        A scalar overall loss value, probably the mean loss over all batches
    components (dict[str, float]):
        A dictionary of component losses to their float values,
        e.g., {"recon": 0.92, "kl": 0.88} for the reconstruction and Kullback-Leibler losses
    """

    loss: float
    components: LossesComponentsDict


class HistoryDict(TypedDict):  # noqa: D101
    train_loss: list[float]
    val_loss: list[float]
    train_components: list[LossesComponentsDict]
    val_components: list[LossesComponentsDict]
    learning_rate: list[float]


def gaussian_lowpass_downsample(x: torch.Tensor, scale: int, kernel_size: int = 5, std: float = 1.0) -> torch.Tensor:
    """
    Apply Gaussian smoothing and then downsample the time series.

    Parameters
    ----------
    x
        Tensor of shape [batch_size, n_days, seq_len, features]
    scale
        Downsampling factor (e.g., 2, 4)
    kernel_size
        Size of Gaussian kernel
    std
        Standard deviation of the Gaussian

    Returns
    -------
        Downsampled tensor
    """
    # Reshape and permute to [batch_size*n_days, features, seq_len]
    batch_size, n_days, seq_len, features = x.shape
    x = x.reshape(batch_size * n_days, seq_len, features)
    x = x.permute(0, 2, 1)

    padding = kernel_size // 2
    channels = x.shape[1]

    # Create Gaussian kernel
    t = torch.arange(kernel_size, device=x.device) - kernel_size // 2
    gauss = torch.exp(-0.5 * (t / std) ** 2)
    gauss /= gauss.sum()
    kernel = gauss.view(1, 1, -1).repeat(channels, 1, 1)  # (C, 1, K)

    # Depthwise conv: same kernel applied per channel
    x = nn.functional.pad(x, (padding, padding), mode="reflect")
    x = nn.functional.conv1d(x, kernel, groups=channels)
    x = x[:, :, ::scale]  # Subsample

    # Reshape and permute to [batch_size, n_days, -1, features]
    x = x.permute(0, 2, 1)
    x = x.reshape(batch_size, n_days, -1, features)
    return x


def multiscale_l1_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    scales: Collection[int] = (8,),
    kernel_size: int = 5,
    std: float = 1.0,
    reduction: str = "mean",
) -> torch.Tensor:
    """
    Compute the multi-scale L1 loss using Gaussian low-pass filtered downsampling.

    Parameters
    ----------
    pred
     Tensor of shape (batch, channels, time)
    target
        Tensor of shape (batch, channels, time)
    scales
        Iterable of downsampling scales (1 = no downsampling); default is 8, which downsamples hh data to 4h resolution
    kernel_size
        Gaussian smoothing parameter
    std
        Gaussian smoothing parameter
    reduction
        'mean', 'sum', or 'none'
    """
    assert pred.shape == target.shape
    loss = torch.tensor(0.0, dtype=torch.float32, device=pred.device)
    for s in scales:
        if s > 1:
            pred_ds = gaussian_lowpass_downsample(pred, s, kernel_size, std)
            target_ds = gaussian_lowpass_downsample(target, s, kernel_size, std)
        else:
            pred_ds = pred
            target_ds = target

        loss += nn.functional.l1_loss(pred_ds, target_ds, reduction=reduction)

    return loss / len(scales)


def vae_loss(
    outputs: dict[str, torch.Tensor],
    targets: torch.Tensor,
    kl_weight: float = 1.0,
    kl_free_bits: float = 0.0,
    scales: Collection[int] = (1,),
    recon_weight: float = 0.0,
    temporal_weight: float = 0.5,
) -> dict[str, torch.Tensor]:
    """
    Calculate loss for VAE model.

    Parameters
    ----------
    outputs
        Dictionary of model outputs
    targets
        Target half-hourly data
    kl_weight
        Weight for KL divergence loss
    kl_free_bits
        value at which to lower-clamp the mean KL loss per dim of the latent space
        KL with free-bits can mitigate against posterior collapse; see Kingma et al (2016).
    scales
        factors at which to downscale before calculating reconstruction losses
    recon_weight
        Weight for VAE reconstruction loss
    temporal_weight
        Weight for temporal coherence loss

    Returns
    -------
        Dictionary of loss components and total loss
    """
    # Extract outputs
    reconstructed = outputs["reconstructed"]
    mu = outputs["mu"]
    logvar = outputs["logvar"]

    # Reconstruction loss
    recon_loss = multiscale_l1_loss(reconstructed, targets, scales=scales, kernel_size=11, std=2.2)
    # setting scales=1 would implement the MAE / L1 loss on the original scale reconstructions

    # KL divergence loss (potentially with free bits)
    kl_loss_per_dim = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp())
    kl_loss_per_dim_batch_mean = kl_loss_per_dim.reshape(-1, mu.shape[-1]).mean(dim=0)
    kl_clamped_per_dim = torch.clamp(kl_loss_per_dim_batch_mean, min=kl_free_bits)

    kl_loss = kl_clamped_per_dim.sum()
    kl_loss /= 10.0  # scale to operate on similar level as reconstruction loss.
    # kl_loss = kl_loss / targets.size(0)  # Normalise by batch size

    # Temporal coherence loss
    # lag-one differences should be similar in target and reconstruction
    pred_diffs = reconstructed[:, :, 1:, :] - reconstructed[:, :, :-1, :]
    target_diffs = targets[:, :, 1:, :] - targets[:, :, :-1, :]
    # temporal_loss = nn.functional.mse_loss(pred_diffs, target_diffs) # performs loss normalisation internally
    temporal_loss = nn.functional.l1_loss(pred_diffs, target_diffs)  # performs loss normalisation internally

    # Total loss
    total_loss = kl_weight * kl_loss + recon_weight * recon_loss + temporal_weight * temporal_loss

    return {
        "total": total_loss,
        "recon": recon_loss,
        "kl": kl_loss,
        "temporal": temporal_loss,
    }


def train_epoch(
    model: VAE,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: str,
    kl_weight: float = 1.0,
    kl_free_bits: float = 0.0,
    recon_downsampling_scales: Collection[int] = (1,),
    recon_weight: float = 0.0,
    temporal_weight: float = 0.5,
    clip_grad_norm: float | None = None,
) -> LossesDict:
    """
    Train model for one epoch.

    Parameters
    ----------
    model
        VAE model
    train_loader
        DataLoader for training data
    optimizer
        Optimizer
    device
        Device to use
    kl_weight
        Weight for KL divergence loss
    kl_free_bits
        value at which to lower-clamp the mean KL loss per dim of the latent space
    recon_downsampling_scales
        factors at which to downscale reconstructions
    recon_weight
        Weight for VAE reconstruction loss
    temporal_weight
        Weight for temporal coherence loss
    clip_grad_norm
        Maximum norm for gradient clipping

    Returns
    -------
        Dictionary of average losses
    """
    model.train()
    total_loss = 0.0
    loss_components = {
        "recon": 0.0,
        "kl": 0.0,
        "temporal": 0.0,
    }

    for batch in train_loader:
        # Get data
        hh_data = batch["data"].to(device)
        daily_data = batch["aggregate"].to(device)
        start_time = batch["start_time"].to(device)
        end_time = batch["end_time"].to(device)

        # Forward pass
        optimizer.zero_grad()
        outputs = model(hh_data, daily_data, start_time, end_time)

        # Calculate loss
        losses = vae_loss(
            outputs=outputs,
            targets=hh_data,
            kl_weight=kl_weight,
            kl_free_bits=kl_free_bits,
            scales=recon_downsampling_scales,
            recon_weight=recon_weight,
            temporal_weight=temporal_weight,
        )

        # Backward pass
        losses["total"].backward()  # type: ignore

        # Gradient clipping if specified
        if clip_grad_norm is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad_norm)

        # Update weights
        optimizer.step()

        # Accumulate losses
        total_loss += losses["total"].item()
        for key in loss_components:
            loss_components[key] += losses[key].item()

    # Calculate averages
    num_batches = len(train_loader)
    avg_loss = total_loss / num_batches
    avg_components = cast(LossesComponentsDict, {key: loss_components[key] / num_batches for key in loss_components})

    return {"loss": avg_loss, "components": avg_components}


def validate(
    model: VAE,
    val_loader: DataLoader,
    device: str,
    kl_weight: float = 1.0,
    kl_free_bits: float = 0.0,
    recon_downsampling_scales: Collection[int] = (1,),
    recon_weight: float = 0.0,
    temporal_weight: float = 0.5,
) -> LossesDict:
    """
    Validate model.

    Parameters
    ----------
        model: VAE model
        val_loader: DataLoader for validation data
        device: Device to use
        kl_weight: Weight for KL divergence loss
        kl_free_bits: value at which to lower-clamp the mean KL loss per dim of the latent space
        recon_downsampling_scales: factors at which to downscale reconstructions
        recon_weight: Weight for VAE reconstruction loss
        temporal_weight: Weight for temporal coherence loss

    Returns
    -------
        Dictionary of average losses
    """
    model.eval()
    total_loss = 0.0
    loss_components = {
        "recon": 0.0,
        "kl": 0.0,
        "temporal": 0.0,
    }

    with torch.no_grad():
        for batch in val_loader:
            # Get data
            hh_data = batch["data"].to(device)
            daily_data = batch["aggregate"].to(device)
            start_time = batch["start_time"].to(device)
            end_time = batch["end_time"].to(device)

            # Forward pass
            outputs = model(hh_data, daily_data, start_time, end_time)

            # Calculate loss
            losses = vae_loss(
                outputs=outputs,
                targets=hh_data,
                kl_weight=kl_weight,
                kl_free_bits=kl_free_bits,
                scales=recon_downsampling_scales,
                recon_weight=recon_weight,
                temporal_weight=temporal_weight,
            )

            # Accumulate losses
            total_loss += losses["total"].item()
            for key in loss_components:
                loss_components[key] += losses[key].item()

    # Calculate averages
    num_batches = len(val_loader)
    avg_loss = total_loss / num_batches
    avg_components = cast(LossesComponentsDict, {key: loss_components[key] / num_batches for key in loss_components})

    return {"loss": avg_loss, "components": avg_components}


def kl_annealing_scheduler(
    epoch: int,
    start_weight: float = 0.0,
    target_weight: float = 1.0,
    annealing_delay: int = 0,
    annealing_epochs: int = 10,
    annealing_strategy: str | None = None,
) -> float:
    """
    Calculate KL weight for annealing.

    Parameters
    ----------
        epoch: Current epoch
        start_weight: Starting weight
        target_weight: Target weight
        annealing_delay: Number of epochs before which we start annealing
        annealing_epochs: Number of epochs for annealing
        annealing_strategy: Strategy for annealing ('linear', 'sigmoid', 'cyclical', or None)

    Returns
    -------
        KL weight for current epoch
    """
    if epoch < annealing_delay:
        weight = 0.0
    else:
        adjusted_epoch = epoch - annealing_delay
        if annealing_strategy == "linear":
            # Linear annealing
            weight = min(
                target_weight, start_weight + (target_weight - start_weight) * max(adjusted_epoch, 0) / annealing_epochs
            )

        elif annealing_strategy == "sigmoid":
            # Sigmoid annealing
            if annealing_epochs > 0:
                x = 10 * (adjusted_epoch - annealing_epochs / 2) / annealing_epochs
                weight = target_weight / (1 + np.exp(-x))
            else:
                weight = target_weight

        elif annealing_strategy == "cyclical":
            # Cyclical annealing
            if annealing_epochs > 0:
                cycle_size = annealing_epochs // 2
                cycle = adjusted_epoch // cycle_size
                position = adjusted_epoch % cycle_size
                if cycle % 2 == 0:  # Even cycle: anneal
                    weight = start_weight + (target_weight - start_weight) * position / cycle_size
                else:  # Odd cycle: use target weight
                    weight = target_weight
            else:
                weight = target_weight

        elif annealing_strategy is None:
            # Default: no annealing
            weight = target_weight
        else:
            warnings.warn("Incorrect specification of annealing_strategy - defaulting to None", stacklevel=2)
            weight = target_weight

    return weight


def train_model(
    model: VAE,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5,
    kl_annealing: bool = True,
    kl_annealing_delay: int = 0,
    kl_annealing_epochs: int = 20,
    kl_annealing_strategy: str = "linear",
    kl_free_bits: float = 0.0,
    recon_downsampling_scales: Collection[int] = (1,),
    recon_weight: float = 0.0,
    temporal_weight: float = 0.5,
    device: str = "cuda",
    log_dir: Path | None = None,
    checkpoint_path: Path | None = None,
    early_stopping: bool = True,
    early_stopping_patience: int = 50,
    clip_grad_norm: float | None = None,
    scheduler_factor: float = 0.5,
    scheduler_patience: int = 5,
) -> tuple[VAE, HistoryDict]:
    """
    Train VAE model.

    Parameters
    ----------
    model
        VAE model
    train_loader
         DataLoader for training data
    val_loader
        DataLoader for validation data
    num_epochs
        Number of epochs to train
    learning_rate
        Learning rate
    weight_decay
        Weight decay for optimizer
    kl_annealing
        Whether to use KL annealing
    kl_annealing_delay
        Number of epochs before which we start annealing
    kl_annealing_epochs
        Number of epochs for KL annealing
    kl_annealing_strategy
        Strategy for KL annealing
    kl_free_bits
        value at which to lower-clamp the mean KL loss per dim of the latent space
    recon_downsampling_scales
        factors at which to downscale reconstructions
    recon_weight
        Weight for VAE reconstruction loss
    temporal_weight
        Weight for temporal coherence loss
    device
        Device to use
    log_dir
        Directory for TensorBoard logs
    checkpoint_path
        Path to save model checkpoints
    early_stopping
        Whether to use early stopping
    early_stopping_patience
        Patience for early stopping
    clip_grad_norm
        Maximum norm for gradient clipping
    scheduler_factor
        Factor for learning rate scheduler
    scheduler_patience
        Patience for learning rate scheduler

    Returns
    -------
        Tuple of (trained model, training history dict)
    """
    # Move model to device
    model = model.to(device)

    # Create optimizer
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    # Create learning rate scheduler
    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=scheduler_factor,
        patience=scheduler_patience,
    )

    # Create TensorBoard writer if log_dir is provided
    writer = SummaryWriter(log_dir) if log_dir is not None else None  # type: ignore

    # Initialize training history
    history: HistoryDict = {"train_loss": [], "val_loss": [], "train_components": [], "val_components": [], "learning_rate": []}

    # Initialize early stopping variables
    best_val_loss = float("inf")
    best_epoch = 0

    # Training loop
    for epoch in range(num_epochs):
        # Calculate KL weight for annealing
        kl_weight = 1.0
        if kl_annealing:
            kl_weight = kl_annealing_scheduler(
                epoch=epoch,
                start_weight=0.0,
                target_weight=1.0,
                annealing_delay=kl_annealing_delay,
                annealing_epochs=kl_annealing_epochs,
                annealing_strategy=kl_annealing_strategy,
            )

        # Train for one epoch
        train_results = train_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            device=device,
            kl_weight=kl_weight,
            kl_free_bits=kl_free_bits,
            recon_downsampling_scales=recon_downsampling_scales,
            recon_weight=recon_weight,
            temporal_weight=temporal_weight,
            clip_grad_norm=clip_grad_norm,
        )

        # Validate
        val_results = validate(
            model=model,
            val_loader=val_loader,
            device=device,
            kl_weight=kl_weight,
            kl_free_bits=kl_free_bits,
            recon_downsampling_scales=recon_downsampling_scales,
            recon_weight=recon_weight,
            temporal_weight=temporal_weight,
        )

        # Update learning rate scheduler
        scheduler.step(val_results["loss"])

        # Log to TensorBoard if writer is provided
        if writer is not None:
            writer.add_scalar("Loss/train", train_results["loss"], epoch)  # type: ignore
            writer.add_scalar("Loss/val", val_results["loss"], epoch)  # type: ignore

            for key in train_results["components"]:
                writer.add_scalar(f"Components/train_{key}", train_results["components"][key], epoch)  # type: ignore
                writer.add_scalar(f"Components/val_{key}", val_results["components"][key], epoch)  # type: ignore

            writer.add_scalar("KL_weight", kl_weight, epoch)  # type: ignore
            writer.add_scalar("Learning_rate", optimizer.param_groups[0]["lr"], epoch)  # type: ignore

        # Update history
        history["train_loss"].append(train_results["loss"])
        history["val_loss"].append(val_results["loss"])
        history["train_components"].append(train_results["components"])
        history["val_components"].append(val_results["components"])
        history["learning_rate"].append(optimizer.param_groups[0]["lr"])

        # Log progress
        logger.info(
            f"Epoch {epoch + 1}/{num_epochs} - "
            f"Train Loss: {train_results['loss']:.4f}, "
            f"Val Loss: {val_results['loss']:.4f}, "
            f"KL Weight: {kl_weight:.4f}, "
            f"LR: {optimizer.param_groups[0]['lr']:.6f}, "
            f"checkpoint at epoch {best_epoch}"
        )

        # Check for best model
        if val_results["loss"] < best_val_loss:
            best_val_loss = val_results["loss"]
            best_epoch = epoch

            # Save checkpoint if path is provided
            if checkpoint_path is not None:
                torch.save(model.state_dict(), checkpoint_path)
                logger.info(f"Saved checkpoint at epoch {epoch + 1}")

        # Early stopping
        if (
            early_stopping
            and epoch - best_epoch >= early_stopping_patience
            and epoch - early_stopping_patience >= kl_annealing_epochs + kl_annealing_delay
        ):  # do at least one round of annealing
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break

    # Load best model if checkpoint path is provided
    if checkpoint_path is not None and checkpoint_path.exists():
        model.load_state_dict(torch.load(checkpoint_path))
        logger.info(f"Loaded best model from epoch {best_epoch + 1}")

    # Close TensorBoard writer if it was created
    if writer is not None:
        writer.close()  # type: ignore

    return model, history


def vae_training(
    model: VAE,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs_vae: int = 30,
    learning_rate_vae: float = 1e-3,
    weight_decay: float = 1e-5,
    kl_annealing: bool = True,
    kl_annealing_delay: int = 0,
    kl_annealing_epochs: int = 20,
    kl_annealing_strategy: str = "linear",
    kl_free_bits: float = 0.0,
    recon_downsampling_scales: tuple = (1,),
    temporal_weight: float = 0.5,
    device: str = "cuda",
    log_dir: Path | None = None,
    checkpoint_path: Path | None = None,
    early_stopping: bool = True,
) -> tuple[VAE, dict[str, HistoryDict]]:
    """
    Train VAE model, creating checkpoints and setting up log directories for Tensorboard.

    Optionally use KL annealing and/or free bit strategies to avoid posterior collapse.

    Parameters
    ----------
    model
        VAE model
    train_loader
        DataLoader for training data
    val_loader
        DataLoader for validation data
    num_epochs_vae
        Number of epochs to train VAE
    learning_rate_vae
        Learning rate for VAE training
    weight_decay
        Weight decay for optimizer
    kl_annealing
        Whether to use KL annealing
    kl_annealing_delay
        Number of epochs before which we start annealing
    kl_annealing_epochs
        Number of epochs for KL annealing
    kl_annealing_strategy
        Strategy for KL annealing
    kl_free_bits
        value at which to lower-clamp the mean KL loss per dim of the latent space
    recon_downsampling_scales
        factors at which to downscale reconstructions
    temporal_weight
        Weight to assign to temporal coherence component of loss
    device
        Device to use
    log_dir
        Directory for TensorBoard logs
    checkpoint_path
        Path to save model checkpoints
    early_stopping
        Whether to use early stopping  -- default behaviour is to stop if no better val results achieved in last 15 epochs

    Returns
    -------
        Tuple of (trained model, training history dict)
    """
    # Move model to device
    model = model.to(device)

    # Create log directories
    if log_dir is not None:
        vae_log_dir = log_dir / "vae"
        vae_log_dir.mkdir(exist_ok=True, parents=True)
    else:
        vae_log_dir = None

    # Create checkpoint paths
    if checkpoint_path is not None:
        checkpoint_dir = checkpoint_path.parent if checkpoint_path.is_file() else checkpoint_path
        checkpoint_name = checkpoint_path.name
        vae_checkpoint = checkpoint_dir / f"vae_{checkpoint_name}"
    else:
        vae_checkpoint = None

    # Initialize history
    history: dict[str, HistoryDict] = {}

    logger.info("=== Training VAE ===")
    # Train VAE
    _, vae_history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs_vae,
        learning_rate=learning_rate_vae,
        weight_decay=weight_decay,
        kl_annealing=kl_annealing,
        kl_annealing_delay=kl_annealing_delay,
        kl_annealing_epochs=kl_annealing_epochs,
        kl_annealing_strategy=kl_annealing_strategy,
        kl_free_bits=kl_free_bits,
        recon_downsampling_scales=recon_downsampling_scales,
        recon_weight=1.0,
        temporal_weight=temporal_weight,
        device=device,
        log_dir=vae_log_dir,
        checkpoint_path=vae_checkpoint,
        early_stopping=early_stopping,
    )

    history["vae"] = vae_history

    return model, history


def plot_loss_components(
    history: dict[str, list[dict[str, float]]],
    components: list[str] | None = None,
    save_path: str | None = None,
    show_plot: bool = True,
    logscale_y: bool = False,
) -> Figure:
    """
    Plot individual loss components.

    Parameters
    ----------
    history
        Dictionary containing loss component history
    components
        List of components to plot (defaults to all)
    save_path
        Path to save the figure
    show_plot
        Whether to display the plot
    logscale_y
        Whether to use a log scale on the y-axis

    Returns
    -------
        Matplotlib figure object
    """
    train_hist = history["train_components"]
    val_hist = history["val_components"]

    # Extract components if not specified
    if components is None:
        components = list(train_hist[0].keys())

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    n_epochs = len(train_hist)
    # Plot each component
    epochs = list(range(1, n_epochs + 1))

    for component in components:
        train_values = [epoch_data.get(component, 0) for epoch_data in train_hist]
        val_values = [epoch_data.get(component, 0) for epoch_data in val_hist]

        ax.plot(epochs, train_values, "-", label=f"Train {component}")
        ax.plot(epochs, val_values, "--", label=f"Val {component}")

    # If log-scale requested, change y-axis here:
    if logscale_y:
        ax.set_yscale("log")

    # Add labels and title
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss Component Value")
    ax.set_title("Loss Components")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save figure if path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    # Show plot if requested
    if show_plot:
        plt.show()
    else:
        plt.close()

    return fig
