#!/usr/bin/env python3
"""Sanitized benchmark fixture: single-purpose reply helper."""

from __future__ import annotations

import os
import re
import subprocess
import threading
from typing import Mapping



BUZZ_CLI = "/benchmark/bin/buzz-placeholder"
MAX_CONTENT_CHARS = 4000
ALLOWED_CHANNELS = frozenset(
    {
        "test-channel-01",
        "test-channel-02",
        "test-channel-03",
        "test-channel-04",
        "test-channel-05",
        "test-channel-06",
        "test-channel-07",
        "test-channel-08",
    }
)

_attempted_replies: set[str] = set()
_attempt_lock = threading.Lock()


def validate_reply(
    channel_id: str,
    reply_to: str,
    content: str,
    *,
    trusted_channel_id: str | None,
) -> tuple[str, str, str]:
    """Validate a reply against the ACP-injected channel and Genie allowlist."""
    if not isinstance(trusted_channel_id, str) or trusted_channel_id not in ALLOWED_CHANNELS:
        raise ValueError("Trusted Buzz session channel is unavailable; reply refused.")
    if channel_id != trusted_channel_id:
        raise ValueError("Reply channel must match the current Buzz session channel.")
    if not isinstance(channel_id, str) or channel_id not in ALLOWED_CHANNELS:
        raise ValueError("Channel is not in Genie's permitted Buzz channel list.")
    if not isinstance(reply_to, str) or re.fullmatch(r"[0-9a-f]{64}", reply_to) is None:
        raise ValueError("reply_to must be a 64-character lowercase event id.")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Reply content must not be blank.")
    if len(content) > MAX_CONTENT_CHARS:
        raise ValueError(f"Reply exceeds the {MAX_CONTENT_CHARS}-character limit.")
    return channel_id, reply_to, content


def _credential_environment(source: Mapping[str, str]) -> dict[str, str]:
    """Pass only the minimum environment needed by the fixed Buzz CLI command."""
    private_key = source.get("BUZZ_PRIVATE_KEY", "")
    relay_url = source.get("BUZZ_RELAY_URL", "")
    if not private_key or not relay_url:
        raise RuntimeError("Buzz credentials are unavailable; reply was not sent.")
    env = {
        "HOME": "/benchmark",
        "PATH": "/benchmark/bin:/usr/bin:/bin",
        "BUZZ_PRIVATE_KEY": private_key,
        "BUZZ_RELAY_URL": relay_url,
    }
    auth_tag = source.get("BUZZ_AUTH_TAG", "")
    if auth_tag:
        env["BUZZ_AUTH_TAG"] = auth_tag
    return env


def send_reply(
    channel_id: str,
    reply_to: str,
    content: str,
    *,
    env: Mapping[str, str] | None = None,
    runner=None,
) -> str:
    """Post exactly one reply to the ACP-provided channel; never invoke a shell."""
    source = os.environ if env is None else env
    trusted_channel_id = source.get("BUZZ_GIT_ORIGIN_CHANNEL_ID")
    channel_id, reply_to, content = validate_reply(
        channel_id, reply_to, content, trusted_channel_id=trusted_channel_id
    )
    process_env = _credential_environment(source)
    run = runner or subprocess.run
    with _attempt_lock:
        if reply_to in _attempted_replies:
            raise RuntimeError("A reply attempt already exists for this event; do not retry blindly.")
        # Fail closed after an ambiguous transport error: duplicate posting is worse than
        # requiring a fresh owner mention to retry.
        _attempted_replies.add(reply_to)
        try:
            result = run(
                [BUZZ_CLI, "messages", "send", "--channel", channel_id, "--content", "-", "--reply-to", reply_to],
                input=content,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
                env=process_env,
                shell=False,
                cwd="/benchmark",
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Buzz send timed out; check the channel before attempting another reply.") from exc
        except OSError as exc:
            raise RuntimeError("Buzz sender could not start; reply was not confirmed.") from exc
    if result.returncode != 0:
        raise RuntimeError("Buzz rejected the reply; do not retry this event blindly.")
    return "Reply sent to Buzz."
