"""
SkillMatch AI - Gunicorn Production Configuration
Used in Linux/Container production environments with Uvicorn worker processes.
"""

import multiprocessing
import os

# Server socket
port = os.getenv("PORT", "8000")
bind = os.getenv("BIND", f"0.0.0.0:{port}")
backlog = 2048

# Worker processes
# Standard formula: 2 * CPU + 1, capped by default or overridden by WEB_CONCURRENCY
default_workers = max(2, min(multiprocessing.cpu_count() * 2 + 1, 8))
workers = int(os.getenv("WEB_CONCURRENCY", os.getenv("WORKERS", str(default_workers))))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = 30

# Process naming
proc_name = "skillmatch-ai-server"

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(D)s µs)'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None


def on_starting(server):
    print("=" * 68)
    print(">> SkillMatch AI Gunicorn Master Process Starting")
    print(f">> Binding Address : {bind}")
    print(f">> Worker Count    : {workers} (UvicornWorker)")
    print(f">> Timeout Config  : {timeout}s")
    print("=" * 68)


def post_fork(server, worker):
    print(f">> Worker spawned (PID: {worker.pid})")


def worker_exit(server, worker):
    print(f">> Worker exiting (PID: {worker.pid})")
