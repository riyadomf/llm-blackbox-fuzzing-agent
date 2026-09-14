"""Minimal .env loader.

Format: `KEY=value` per line, `#` comments, blank lines ignored, optional
`export ` prefix, optional surrounding single or double quotes.

Values already present in the real environment win, so
`LLM_BACKEND=openai ./run.sh` overrides the file without editing it.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path | None = None, override: bool = False) -> dict[str, str]:
    """Read .env into os.environ. Returns the keys it set (values not logged)."""
    p = Path(path) if path else REPO_ROOT / ".env"
    if not p.exists():
        return {}

    applied: dict[str, str] = {}
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if not key:
            continue
        # Real environment wins unless explicitly overridden, so a one-off
        # `VAR=x` on the command line beats the file.
        if override or key not in os.environ:
            os.environ[key] = val
        applied[key] = val
    return applied


def describe_env() -> str:
    """Which credential-bearing variables are set, WITHOUT printing values."""
    watched = ("LLM_BACKEND", "LLM_MODEL", "OPENAI_API_KEY", "OPENAI_BASE_URL",
               "CLAUDE_CODE_OAUTH_TOKEN")
    out = []
    for k in watched:
        v = os.environ.get(k)
        if not v:
            out.append(f"{k}=<unset>")
        elif "KEY" in k or "TOKEN" in k:
            out.append(f"{k}=<set, {len(v)} chars>")
        else:
            out.append(f"{k}={v}")
    return "  ".join(out)
