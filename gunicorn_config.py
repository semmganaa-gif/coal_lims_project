# gunicorn_config.py
# Coal LIMS - Production Gunicorn Configuration
# Usage: gunicorn -c gunicorn_config.py "app:create_app()"

import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
threads = 2
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 120
graceful_timeout = 30
keepalive = 5

# Process naming
proc_name = "coal_lims"

# Server mechanics
daemon = False
pidfile = os.getenv("GUNICORN_PIDFILE", "/var/run/coal_lims.pid")
user = None
group = None
umask = 0
tmp_upload_dir = None

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # "-" = stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")    # "-" = stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (uncomment if using SSL directly with Gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = "TLS"

# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass

def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    pass

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    pass

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called when the number of workers has been changed."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass
