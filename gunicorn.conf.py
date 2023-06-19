from yaml import safe_load

with open("/app/logconf.yaml") as f:
    logconf = safe_load(f)

logconfig_dict = logconf
access_log_format = '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
wsgi_app = 'odinapi.api:app'
bind = "0.0.0.0:8080"
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https'}
forwarded_allow_ips = '*'