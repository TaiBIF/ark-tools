# Gunicorn configuration for production
import os

# Binding
bind = "0.0.0.0:8001"

# Workers
workers = 2
worker_class = "sync"

# Logging
# Use '-' to log to stdout/stderr (recommended for Docker)
# Or set LOG_TO_FILE=1 to log to files
if os.getenv("LOG_TO_FILE"):
    accesslog = "/var/log/gunicorn/access.log"
    errorlog = "/var/log/gunicorn/error.log"
else:
    accesslog = "-"
    errorlog = "-"

loglevel = "info"

# Access log format
# %h - remote address
# %l - '-'
# %u - user name
# %t - date of the request
# %r - status line (e.g. GET / HTTP/1.1)
# %s - status
# %b - response length
# %f - referer
# %a - user agent
# %T - request time in seconds
# %D - request time in microseconds
access_log_format = '%({x-forwarded-for}i)s %(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(T)ss'

# Timeout
timeout = 30
graceful_timeout = 30

# Keep alive
keepalive = 2
