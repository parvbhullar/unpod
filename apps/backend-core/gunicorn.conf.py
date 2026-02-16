# Gunicorn configuration file for Unpod Backend
# This configuration is optimized for stability and prevents 504 timeouts

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# Formula: 2 * num_cores + 1 (for a 4 core machine = 9 workers)
# But we use 4 workers to be conservative with memory
workers = 4
worker_class = "sync"
threads = 2
worker_connections = 1000

# Worker timeout - CRITICAL: Increase this to handle slow external API calls
# This must be higher than the requests timeout (30s) we set in the code
timeout = 120  # 2 minutes to handle slow external services
graceful_timeout = 30
keepalive = 5

# Worker recycling - CRITICAL: This prevents memory leaks
# Workers are restarted after handling this many requests
max_requests = 1000  # Restart worker after 1000 requests
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Memory limit per worker (in bytes) - kill workers using too much memory
# This requires the 'gevent' worker class or third-party extensions
# limit_request_line = 4094
# limit_request_fields = 100
# limit_request_field_size = 8190

# Logging
accesslog = "-"  # Log to stdout (captured by systemd/journald)
errorlog = "-"   # Log to stderr (captured by systemd/journald)
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "unpod-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed, configure here)
# keyfile = None
# certfile = None

# Hooks for monitoring
def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    # Close database connections in the child process
    # Django will re-open them as needed
    from django.db import connections
    for conn in connections.all():
        conn.close()

    # Reset MongoDB connection - CRITICAL for multi-process environments
    # MongoDB connections are not fork-safe
    try:
        from unpod.common.mongodb import MongoDBQueryManager
        MongoDBQueryManager.reset_connection()
        server.log.info(f"Worker {worker.pid}: MongoDB connection reset")
    except Exception as e:
        server.log.warning(f"Worker {worker.pid}: Could not reset MongoDB connection: {e}")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    worker.log.info("worker received SIGABRT signal")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    # Clean up database connections
    from django.db import connections
    for conn in connections.all():
        conn.close()

    # Clean up MongoDB connection
    try:
        from unpod.common.mongodb import MongoDBQueryManager
        MongoDBQueryManager.reset_connection()
    except Exception:
        pass

def child_exit(server, worker):
    """Called when a worker process is terminated."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called when the number of workers changes."""
    pass

def on_exit(server):
    """Called just before the master process exits."""
    pass
