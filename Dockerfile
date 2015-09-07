from ubuntu:latest
run apt-get update && apt-get install -y \
    python-pip \
    python-dev
run pip install flask flask-bootstrap
copy src/ /app/
expose 5000
cmd python /app/api.py
