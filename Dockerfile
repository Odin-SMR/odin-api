FROM python:3.6
COPY requirements_python36.apt /app/
WORKDIR /app
RUN set -x && \
    apt-get update && xargs apt-get install -y < requirements_python36.apt

COPY dependencies/ /dependencies/

# swagger
RUN cd /dependencies && tar -xzf swagger-ui-2.2.8.tar.gz && \
    mkdir -p /swagger-ui && \
    cp -r swagger-ui-2.2.8/dist/* /swagger-ui/ && \
    sed -i 's#<title>Swagger UI</title>#<title>Odin rest API</title>#g' /swagger-ui/index.html && \
    sed -i 's#http://petstore.swagger.io/v2/swagger.json#/rest_api/v5/spec#g' /swagger-ui/index.html && \
    rm -rf swagger-ui*

COPY requirements.txt /app
RUN pip install --no-binary=h5py -r requirements.txt
COPY src/odinapi /app/odinapi/
COPY src/scripts /app/scripts/
COPY src/examples /app/odinapi/static/examples/
EXPOSE 5000
CMD gunicorn -w 4 -b 0.0.0.0:5000 -k gevent --timeout 540 odinapi.api:app
