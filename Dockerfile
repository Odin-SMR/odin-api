from ubuntu:16.04
run apt-get update && apt-get install -y \
    gfortran \
    python-numpy \
    python-psycopg2 \
    python-matplotlib \
    python-dev \
    python-pip \
    python-pygresql \
    python-scipy \
    python-h5py \
    libhdf5-serial-dev \
    libhdf4-dev \
    git \
    curl \
    m4 \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

run pip install cython python-hdf4 fortranformat
RUN pip install setuptools --upgrade

run pip install pyephem spacepy pyproj

#************* DEPENDENCIES
ADD dependencies/ /dependencies/
#szip dependency
RUN cd /dependencies && tar -xzf szip-2.1.tar.gz && \
    cd szip-2.1 && \
    ./configure && \
    make && \
    make install && \
    cd .. && rm -rf szip-2.1*

#hdf5 dependency
RUN cd /dependencies && tar -xzf hdf5-1.8.16.tar.gz && \
    cd hdf5-1.8.16 && \
    ./configure && \
    make && \
    make install

#zlib dependency
RUN cd /dependencies && tar -xzf zlib-1.2.8.tar.gz && \
    cd zlib-1.2.8 && \
    ./configure && \
    make && \
    make install && \
    cd .. && rm -rf zlib-1.2.8*

#Netcdf4-c
RUN export CPPFLAGS=-I/dependencies/hdf5-1.8.16/hdf5/include \
    LDFLAGS=-L/dependencies/hdf5-1.8.16/hdf5/lib \
    LD_LIBRARY_PATH=/dependencies/hdf5-1.8.16/hdf5/lib && \
    cd /dependencies && tar -xzf netcdf-c-4.3.3.1.tar.gz && \
    cd netcdf-c-4.3.3.1 && \
    ./configure && \
    make && \
    make install && \
    cd .. && rm -rf netcdf-c-4.3.3.1*

#netcdf4 python
RUN pip install git+https://github.com/Unidata/netcdf4-python.git@v1.2.4rel

#coda
RUN cd /dependencies && tar -xzf coda-2.17.3.tar.gz && \
    cd coda-2.17.3 && \
    ./configure --enable-python PYTHON=/usr/bin/python && \
    make && \
    make install && \
    cd .. && rm -rf coda-2.17.3

#run HDF5_DIR=/dependencies/hdf5-1.8.16/hdf5 pip install h5py

# swagger
RUN cd /dependencies && tar -xzf swagger-ui-2.2.8.tar.gz && \
    mkdir -p /swagger-ui && \
    cp -r swagger-ui-2.2.8/dist/* /swagger-ui/ && \
    sed -i 's#<title>Swagger UI</title>#<title>Odin rest API</title>#g' /swagger-ui/index.html && \
    sed -i 's#http://petstore.swagger.io/v2/swagger.json#/rest_api/v5/spec#g' /swagger-ui/index.html && \
    rm -rf swagger-ui*

COPY odinapi-requirements.txt /tmp/
RUN pip install -r /tmp/odinapi-requirements.txt

ENV TRAVIS=1
# There is a concurency issue in matplotlib font manager caching. Setting
# TRAVIS=1 is a poorly named way to tell matplotlib not to use the font manager
# cache.
# The issue should be fixed in matplotlib 2.x available in Ubuntu 17.04.
# See https://github.com/matplotlib/matplotlib/issues/5226/
# and https://github.com/matplotlib/matplotlib/pull/5276

copy src/ /app/
run cd /app && python setup.py install && python setup.py develop
expose 5000
workdir /app
cmd gunicorn -w 4 -b 0.0.0.0:5000 -k gevent --timeout 180 odinapi.api:app
