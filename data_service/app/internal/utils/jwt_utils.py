"""JSON Web Token validation utils."""

import base64
import datetime
import hmac
import json
from typing import TypedDict

# ruff: noqa: D101, D102


class JwtHeader(TypedDict):
    typ: str
    alg: str


class JwtPayload(TypedDict):
    aud: str
    jti: str
    iat: datetime.datetime
    nbf: datetime.datetime
    exp: datetime.datetime
    sub: int
    scopes: list[str]


def decode_jwt(jwt_str: str) -> tuple[JwtHeader, JwtPayload, str]:
    """
    Decode a JSON Web token and separate into header, payload and signature components.

    This will also parse timestamps into UTC timezone.

    Parameters
    ----------
    jwt_str
        JWT String in the form "header.payload.signature" encoded in base64

    Returns
    -------
    JwtHeader, JwtPayload, str
        Header, Payload and signature as python dictionaries.
    """
    header_raw, payload_raw, signature = jwt_str.split(".")
    header = json.loads(base64.b64decode(header_raw))
    payload = json.loads(base64.b64decode(payload_raw))
    payload["iat"] = datetime.datetime.fromtimestamp(float(payload["iat"]), tz=datetime.UTC)
    payload["nbf"] = datetime.datetime.fromtimestamp(float(payload["nbf"]), tz=datetime.UTC)
    payload["exp"] = datetime.datetime.fromtimestamp(float(payload["exp"]), tz=datetime.UTC)
    return header, payload, signature


def validate_jwt(jwt_str: str, aud: str | None = None, scope: str | None = None, at: datetime.datetime | None = None) -> bool:
    """
    Validate a JWT, throwing if it fails validation.

    Does not currently check the signature of the token.

    Parameters
    ----------
    jwt_str
        JSON Web Token string in form header.payload.signature base64 encoded
    aud
        Audience to check; throws if this is not None and not in the JWT
    scope
        Scope to check; throws if this is not None and not in the JWT Scopes
    at
        Time to check if the JWT will be valid at.

    Returns
    -------
    True
        Successful validation

    Raises
    ------
    ValueError
        Unsuccessful validation
    """
    if at is None:
        at = datetime.datetime.now(tz=datetime.UTC)
    _, payload, _ = decode_jwt(jwt_str)
    if aud is not None and payload["aud"] != aud:
        raise ValueError(f"Expected audience {aud} is not in JWT {payload['aud']}")
    if scope is not None and scope not in payload["scopes"]:
        raise ValueError(f"Expected scope {scope} is not in JWT {payload['scopes']}")

    if at < payload["nbf"]:
        raise ValueError(f"Current time {at} is before the token is valid {payload['nbf']}")

    if at > payload["exp"]:
        raise ValueError(f"Current time {at} is after the token expires {payload['exp']}")
    return True


def generate_jwt(
    aud: str | None = None,
    exp: datetime.datetime | None = None,
    nbf: datetime.datetime | None = None,
    scopes: list[str] | None = None,
    alg: str | None = "HS256",
) -> bytes:
    """
    Generate a JSON Web Token with a signature.

    This is mostly used for testing the JWT code, but might be useful in future?

    Parameters
    ----------
    aud
        Audience for this token
    exp
        Expiry datetime for this token
    nbf
        Not BeFore datetime for this token
    scopes
        API scopes for which this token is valid
    alg
        Signing algorithm for this token

    Returns
    -------
    bytes
        JWT byte string in the form b64(header).b64(payload).b64(signature)
    """
    header = {"alg": alg, "typ": "JWT"}

    payload = {
        "iss": "elementalpower.co.uk",
        "sub": None,
        "aud": aud,
        "exp": exp.timestamp()
        if exp is not None
        else datetime.datetime(year=2100, month=1, day=1, tzinfo=datetime.UTC).timestamp(),
        "nbf": nbf.timestamp() if nbf is not None else datetime.datetime.now(datetime.UTC).timestamp(),
        "iat": datetime.datetime.now(datetime.UTC),
        "jti": None,
        "scopes": scopes if scopes is not None else [],
    }

    header_encode = base64.b64encode(json.dumps(header).encode("utf-8"))
    payload_encode = base64.b64encode(json.dumps(payload).encode("utf-8"))

    if alg is None:
        signature = b""
    elif alg == "HS256":
        signature = hmac.new(
            key=b"elemental-power-secret", msg=header_encode + b"." + payload_encode, digestmod="sha256"
        ).digest()
    else:
        raise AttributeError(f"Alg must be None or 'HS256' but got {alg}")
    return header_encode + b"." + payload_encode + b"." + signature
