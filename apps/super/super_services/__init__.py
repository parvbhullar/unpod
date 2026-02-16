import os
import random
import sys

from pathlib import Path
from dotenv import load_dotenv

__version__ = os.environ.get("SUPER_VERSION", "") or "0.1-dev"
# if "pytest" in sys.argv or "pytest" in sys.modules or os.getenv("CI"):
#     print("Setting random seed to 42")
#     random.seed(42)

# Load .env from monorepo root (fallback to service-local .env)
_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # super_services/ → super/ → apps/ → root
_root_env = _MONOREPO_ROOT / ".env"
if _root_env.exists():
    load_dotenv(str(_root_env), verbose=True, override=True)
else:
    load_dotenv(verbose=True, override=True)
del load_dotenv
