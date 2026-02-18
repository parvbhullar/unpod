import os
import random
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "super")))

from dotenv import load_dotenv

if "pytest" in sys.argv or "pytest" in sys.modules or os.getenv("CI"):
    print("Setting random seed to 42")
    random.seed(42)

# Load the users .env file into environment variables
load_dotenv(verbose=True, override=True)

del load_dotenv
