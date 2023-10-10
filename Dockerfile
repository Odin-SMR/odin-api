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
    apt-get update && xargs apt-get install -y < requirements_python.apt && \
    apt-get -y upgrade

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY src/odinapi /app/odinapi/
COPY --from=0 /odin/src/odinapi/static /app/odinapi/static

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

COPY gunicorn.conf.py /app/
COPY logconf.yaml /app/

ENTRYPOINT [ "/entrypoint.sh" ]
EXPOSE 8000
CMD gunicorn
