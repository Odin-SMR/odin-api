from yaml import safe_load

with open("/app/logconf.yaml") as f:
    logconf = safe_load(f)

accesslog = "-"
errorlog = "-"
access_log_format = (
    '{"remote":"%(h)s","user":"%(u)s","method":"%(m)s","path":"%(U)s",'
    '"query":"%(q)s","protocol":"%(H)s","status":%(s)s,"bytes":%(b)s,'
    '"referer":"%(f)s","agent":"%(a)s","request_time":%(L)s}'
)
bind = "0.0.0.0"
forwarded_allow_ips = "*"
logconfig_dict = logconf
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
timeout = 30
worker_class = "gthread"
workers = 2
threads = 8
preload_app = True
wsgi_app = "odinapi.api:create_app()"
