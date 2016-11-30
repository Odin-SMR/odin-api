from ubuntu:14.04
run apt-get update && apt-get install -y \
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
    build-essential \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

run pip install cython python-hdf4 fortranformat

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
    ./configure --enable-threadsafe --disable-hl && \
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
RUN git clone https://github.com/Unidata/netcdf4-python.git && \
    cd netcdf4-python && \
    cp setup.cfg.template setup.cfg && \
    python setup.py build && \
    python setup.py install && \
    cd .. && rm -rf netcdf4-python*

#coda
RUN cd /dependencies && tar -xzf coda-2.17.3.tar.gz && \
    cd coda-2.17.3 && \
    ./configure --enable-python PYTHON=/usr/bin/python && \
    make && \
    make install && \
    cd .. && rm -rf coda-2.17.3

#run HDF5_DIR=/dependencies/hdf5-1.8.16/hdf5 pip install h5py

run pip install click==6.6                # via flask
run pip install dominate==2.3.0           # via flask-bootstrap
run pip install flasgger==0.5.13
run pip install flask-bootstrap==3.3.7.0
run pip install flask==0.11.1
run pip install functools32==3.2.3-2      # via jsonschema
run pip install itsdangerous==0.24        # via flask
run pip install Jinja2==2.8               # via flask
run pip install jsonschema==2.5.1         # via flasgger
run pip install MarkupSafe==0.23          # via jinja2
run pip install mistune==0.7.3            # via flasgger
run pip install pycrypto==2.6.1
run pip install pymongo==3.3.1
run pip install PyYAML==3.12              # via flasgger
run pip install sqlalchemy==1.1.4
run pip install visitor==0.1.3            # via flask-bootstrap
run pip install Werkzeug==0.11.11         # via flask

copy src/ /app/
run cd /app && python setup.py install && python setup.py develop
expose 5000
cmd python -m odinapi.api
