import os
import random
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "super")))

from pathlib import Path
from dotenv import load_dotenv

if "pytest" in sys.argv or "pytest" in sys.modules or os.getenv("CI"):
    print("Setting random seed to 42")
    random.seed(42)

# Load .env from monorepo root (fallback to service-local .env)
_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent  # super/ → apps/ → root
_root_env = _MONOREPO_ROOT / ".env"
if _root_env.exists():
    load_dotenv(str(_root_env), verbose=True, override=True)
else:
    load_dotenv(verbose=True, override=True)

del load_dotenv
