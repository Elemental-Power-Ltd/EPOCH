import logging

logger = logging.getLogger("default")

_EPOCH_VERSION: str | None = None


def get_epoch_version() -> str:
    """
    Get the version of the epoch.

    Returns
    -------
        A version string (probably Major.Minor.Patch)

    """
    global _EPOCH_VERSION
    if _EPOCH_VERSION is None:
        import epoch_simulator

        _EPOCH_VERSION = epoch_simulator.__version__  # type: ignore

    return _EPOCH_VERSION
