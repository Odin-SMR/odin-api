from ubuntu:latest
run apt-get update && apt-get install -y \
    python-numpy \
    python-psycopg2 \
    python-matplotlib \
    python-dev \
    python-pip \
    python-pygresql
run pip install flask flask-bootstrap sqlalchemy
copy src/ /app/
expose 5000
cmd python /app/api.py
