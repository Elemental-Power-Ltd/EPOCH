"""
Secret handling code, including API keys and JWT loading.

This should be used wherever you're handling an API key.
"""

import copy
import logging
import os
from pathlib import Path

logger = logging.getLogger()


class SecretDict[K, V](dict):
    """Secret dict with unprintable keys to avoid logging problems."""

    def __repr__(self) -> str:
        """Get a repr version of this dictionary with keys obscured."""
        mock_dict = dict.fromkeys(self.keys(), "********")
        return "SecretDict(" + mock_dict.__repr__() + ")"

    def __str__(self) -> str:
        """Get a stringified version of this dictionary with keys obscured."""
        mock_dict = dict.fromkeys(self.keys(), "********")
        return str(mock_dict)

    def str_unsecret(self) -> str:
        """
        Get an un-secreted version of this dictionary.

        Only do this for debugging or if you specifically know what you're doing.
        """
        return str(dict(self))


def load_secret_from_file(fpath: Path) -> str:
    """
    Load a single secret from a file, stripping whitespac.

    The contents of your file should only be the secret value.
    Extra whitespace is stripped, including newlines and leading spaces.

    Parameters
    ----------
    fpath
        Path of the file to open

    Returns
    -------
    stripped string of the contents of the file.
    """
    with open(fpath) as fi:
        return fi.read().strip()


def load_dotenv(fname: os.PathLike = Path(".env")) -> dict[str, str]:
    """
    Load a set of environment variables from an .env file.

    Mutates the environment variables for this python process, and
    returns them as a dictionary just in case.

    Parameters
    ----------
    fname
        Path to the environment file to load (it's probably ".env")

    Returns
    -------
        environment dictionary, with new keys added.
    """
    fpath = Path(fname).resolve()
    if not fpath.is_file():
        file_name = fpath.name
        for parent in fpath.parents:
            parent_path = parent.joinpath(file_name)
            if parent_path.is_file():
                fpath = parent_path
                break
        else:
            logger.warning(f"Could not find {fname} in the specified location {fpath} or its parents.")
            return {}

    with open(fpath) as fi:
        for line in fi:
            key, value = line.strip().split("=", 1)
            os.environ[key.strip()] = value.strip()
    # turn this into a dict to prevent any trouble with weird types
    return dict(os.environ.items())


def get_secrets_environment(
    overrides: dict[str, str] | None = None, default_directory: Path | None = None
) -> SecretDict[str, str]:
    """
    Get a set of secrets from environment locations, including OS environ and files.

    Takes in key: value pairs from the OS environment, the local `.env` file
    and any specific secrets files (if they exist).
    The order of precedence is
        OS environment < .env < secrets < overrides

    The secrets files should be single-value text files, whose keys are specified in the main
    environment.
    This is mostly useful for docker images, where you can specify the file path in the docker file
    e.g.
    environment:
        EP_VISUAL_CROSSING_API_KEY_FILE="/var/run/secrets/visual_crossing_api_key.txt"

    secrets:
        visual_crossing_api_key:
            file: visual_crossing_api_key.txt
    """
    if default_directory is None:
        default_directory = Path.home() / ".secrets"
    os_environ = dict(copy.deepcopy(os.environ))

    dotenv_environ = load_dotenv()

    total_environ = os_environ | dotenv_environ

    vc_fpath = Path(total_environ.get("EP_VISUAL_CROSSING_API_KEY_FILE", default_directory / "visual_crossing_api_key"))
    try:
        total_environ["VISUAL_CROSSING_API_KEY"] = load_secret_from_file(vc_fpath)
    except FileNotFoundError:
        if "VISUAL_CROSSING_API_KEY" not in total_environ:
            logger.warning(f"Could not find VisualCrossing key in environ, dotenv or {vc_fpath}")

    rn_fpath = Path(total_environ.get("EP_RENEWABLES_NINJA_API_KEY_FILE", default_directory / "renewables_ninja_api_key"))
    try:
        total_environ["RENEWABLES_NINJA_API_KEY"] = load_secret_from_file(rn_fpath)
    except FileNotFoundError:
        if "RENEWABLES_NINJA_API_KEY" not in total_environ:
            logger.warning(f"Could not find RenewablesNinja key in environ, dotenv or {rn_fpath}")

    pg_fpath = Path(total_environ.get("EP_POSTGRES_PASSWORD_FILE", default_directory / "ep_postgres_password"))
    try:
        total_environ["EP_POSTGRES_PASSWORD"] = load_secret_from_file(pg_fpath)
    except FileNotFoundError:
        if "EP_POSTGRES_PASSWORD" not in total_environ:
            logger.warning(f"Could not find Postgres key in environ, dotenv or {pg_fpath}")

    ge_fpath = Path(total_environ.get("EP_GIVENERGY_JWT_FILE", default_directory / "ep_givenergy_jwt"))
    try:
        total_environ["EP_GIVENERGY_JWT"] = load_secret_from_file(ge_fpath)
    except FileNotFoundError:
        if "EP_GIVENERGY_JWT" not in total_environ:
            pass
            # We used to warn on this, but it was too noisy.
            # logger.warning(f"Could not find GivEnergy JWT in environ, dotenv or {ge_fpath}")

    if overrides is not None:
        total_environ = total_environ | overrides

    return SecretDict(total_environ)
