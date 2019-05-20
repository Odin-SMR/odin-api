FROM ubuntu:18.04
RUN sed -i "s#archive.ubuntu.com#archive.mirror.blix.com#" /etc/apt/sources.list
RUN apt update && apt upgrade -y && apt install -y tox python3-pip xvfb mongodb
COPY requirements.apt /app/
WORKDIR /app
RUN set -x && \
    apt-get update && xargs apt-get install -y < requirements.apt
RUN pip3 install numpy==1.15.4
ARG uid=386
RUN useradd jenkins --uid $uid --shell /bin/bash --create-home
USER jenkins
