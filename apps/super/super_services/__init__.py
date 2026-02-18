import os
import random
import sys

from dotenv import load_dotenv

__version__ = os.environ.get("SUPER_VERSION", "") or "0.1-dev"
# if "pytest" in sys.argv or "pytest" in sys.modules or os.getenv("CI"):
#     print("Setting random seed to 42")
#     random.seed(42)

# Load the users .env file into environment variables
load_dotenv(verbose=True, override=True)
del load_dotenv
