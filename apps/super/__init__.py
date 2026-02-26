import os
import random
import sys

_REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
_INNER_SUPER_PACKAGE = os.path.join(_REPO_ROOT, "super")

# Keep inner sources importable when this repository root is imported as the
# top-level `super` package (pytest does this during some collection modes).
if _INNER_SUPER_PACKAGE not in sys.path:
    sys.path.insert(1, _INNER_SUPER_PACKAGE)

_pkg_path = globals().get("__path__")
if isinstance(_pkg_path, list) and _INNER_SUPER_PACKAGE not in _pkg_path:
    _pkg_path.insert(0, _INNER_SUPER_PACKAGE)

from dotenv import load_dotenv

if "pytest" in sys.argv or "pytest" in sys.modules or os.getenv("CI"):
    print("Setting random seed to 42")
    random.seed(42)

# Load the users .env file into environment variables
load_dotenv(verbose=True, override=True)

del load_dotenv
