import os

# Define the work pools we want to create

CURRENT_DIR = os.getcwd()
if CURRENT_DIR.find("workpool_config") == -1:
    CURRENT_DIR = "/opt/scripts"

WORKPOOLS = [
    {
        "name": "call-work-pool",
        "type": "docker",
        "base_job_template": f"{CURRENT_DIR}/call_pool_config.json",
        "concurrency_limit": None,
    }
]
