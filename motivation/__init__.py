"""motivation — does motivational prompt language improve AI agent performance?"""

import os
from pathlib import Path

__version__ = "0.1.0"


def _load_dotenv() -> None:
    """Load a gitignored .env file into os.environ (does not override existing vars)."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv()
