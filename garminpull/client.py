"""Authenticated Garmin Connect session handling.

Login is token-based (via garth, which garminconnect wraps). The first successful
login writes OAuth tokens to a token store directory; subsequent runs resume from
those tokens so credentials and MFA are only needed once until the tokens expire.
"""

from __future__ import annotations

import getpass
import os
from pathlib import Path

from garminconnect import Garmin

DEFAULT_TOKENSTORE = "~/.garminconnect"


def _tokenstore_path(tokenstore: str | None) -> str:
    raw = tokenstore or os.getenv("GARMINTOKENS") or DEFAULT_TOKENSTORE
    return str(Path(raw).expanduser())


def login(
    email: str | None = None,
    password: str | None = None,
    tokenstore: str | None = None,
) -> Garmin:
    """Return a logged-in :class:`Garmin` client.

    Tries to resume from stored tokens first. If that fails, falls back to a full
    email/password login and persists fresh tokens for next time. Credentials come
    from the arguments, then the environment (``GARMIN_EMAIL`` / ``GARMIN_PASSWORD``,
    typically via an optional ``.env``), and are finally prompted for interactively if
    still missing. An MFA one-time code is prompted for on the terminal when required.
    """

    store = _tokenstore_path(tokenstore)

    try:
        client = Garmin()
        client.login(store)
        return client
    except (FileNotFoundError, Exception):  # noqa: BLE001 - any resume failure -> full login
        pass

    email = email or os.getenv("GARMIN_EMAIL") or input("Garmin email: ").strip()
    password = password or os.getenv("GARMIN_PASSWORD") or getpass.getpass("Garmin password: ")
    if not email or not password:
        raise RuntimeError("A Garmin email and password are required to authenticate.")

    client = Garmin(email=email, password=password, return_on_mfa=True)
    result_state, result_data = client.login()
    if result_state == "needs_mfa":
        mfa_code = input("Garmin MFA one-time code: ").strip()
        client.resume_login(result_data, mfa_code)

    Path(store).mkdir(parents=True, exist_ok=True)
    client.garth.dump(store)
    return client
