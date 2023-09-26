FROM node:16
COPY ./src/odinapi/static /odin/src/odinapi/static
COPY ./package*.json /odin
COPY webpack.config.js /odin
WORKDIR /odin
RUN npm install
RUN npm run build

FROM python:3.11-buster
COPY requirements_python.apt /app/
WORKDIR /app
RUN set -x && \
    apt-get update && xargs apt-get install -y < requirements_python.apt

COPY dependencies/ /dependencies/

# swagger
RUN cd /dependencies && tar -xzf swagger-ui-2.2.8.tar.gz && \
    mkdir -p /swagger-ui && \
    cp -r swagger-ui-2.2.8/dist/* /swagger-ui/ && \
    sed -i 's#<title>Swagger UI</title>#<title>Odin rest API</title>#g' /swagger-ui/index.html && \
    sed -i 's#http://petstore.swagger.io/v2/swagger.json#/rest_api/v5/spec#g' /swagger-ui/index.html && \
    rm -rf swagger-ui*

COPY requirements.txt /app

RUN pip install -r requirements.txt
COPY src/odinapi /app/odinapi/
COPY src/scripts /app/scripts/
COPY src/examples /app/odinapi/static/examples/
COPY --from=0 /odin/src/odinapi/static /app/odinapi/static
COPY scripts/compile_nrlmsis.sh .
RUN ./compile_nrlmsis.sh
EXPOSE 5000
CMD gunicorn -w 4 -b 0.0.0.0:5000 -k gevent --timeout 540 odinapi.api:app
