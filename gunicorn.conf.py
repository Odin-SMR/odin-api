from multiprocessing import cpu_count
from yaml import safe_load

with open("/app/logconf.yaml") as f:
    logconf = safe_load(f)

access_log_format = '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
bind = "0.0.0.0"
forwarded_allow_ips = "*"
logconfig_dict = logconf
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
timeout = 350
worker_class = "sync"
workers = cpu_count() + 1
preload_app = True
wsgi_app = "odinapi.api:create_app()"
