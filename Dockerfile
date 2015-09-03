from ubuntu:latest
run apt-get update && apt-get install -y \
    python-numpy \
    python-psycopg2 \
    python-matplotlib \
    python-pip
run pip install flask flask-bootstrap sqlalchemy
expose 5000
cmd python /app/datamodel.py
