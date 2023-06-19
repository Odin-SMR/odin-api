FROM node:16
COPY ./ /odin/
WORKDIR /odin
RUN npm install
RUN npm run build

FROM python:3.8-buster
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

COPY requirements.txt /app/
COPY gunicorn.conf.py /app/
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
COPY logconf.yaml /app/
# --no-binary=h5py is needed because in some ways it may get installed
# netcdf doesn't work if h5py is imported before it in the project
RUN pip install -r requirements.txt
COPY src/odinapi /app/odinapi/
COPY src/scripts /app/scripts/
COPY src/examples /app/odinapi/static/examples/
COPY --from=0 /odin/src/odinapi/static/assets /app/odinapi/static/assets
ENV PYTHONPATH "${PYTHONPATH}:/app/odinapi"
ENTRYPOINT [ "/entrypoint.sh" ]
EXPOSE 8000
CMD gunicorn
