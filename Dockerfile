from ubuntu:latest
run apt-get update && apt-get install -y \
    python-numpy \
    python-psycopg2 \
    python-matplotlib \
    python-dev \
    python-pip \
    python-pygresql \
    python-scipy \
    git \
    curl \
    m4 \
    build-essential && \
    apt-get clean
run pip install flask flask-bootstrap sqlalchemy

#************* DEPENDENCIES 
#szip dependency 
RUN curl ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4/szip-2.1.tar.gz | tar xz && \ 
    cd szip-2.1 && \ 
    ./configure && \ 
    make && \ 
    make install && \
    cd .. && rm -rf szip-2.1*

#hdf5 dependency 
RUN curl ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4/hdf5-1.8.13.tar.gz | tar xz && \ 
    cd hdf5-1.8.13 && \ 
    ./configure && \ 
    make && \ 
    make install

#zlib dependency 
RUN curl ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4/zlib-1.2.8.tar.gz | tar xz && \ 
    cd zlib-1.2.8 && \ 
    ./configure && \ 
    make && \ 
    make install && \
    cd .. && rm -rf zlib-1.2.8*

#Netcdf4-c 
RUN export CPPFLAGS=-I/hdf5-1.8.13/hdf5/include \ 
    LDFLAGS=-L/hdf5-1.8.13/hdf5/lib \ 
    LD_LIBRARY_PATH=/hdf5-1.8.13/hdf5/lib && \ 
    curl ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.3.3.1.tar.gz | tar xz && \ 
    cd netcdf-4.3.3.1 && \ 
    ./configure && \ 
    make && \ 
    make install && \
    cd .. && rm -rf netcdf-4.3.3.1*

#netcdf4 python
RUN git clone https://github.com/Unidata/netcdf4-python.git && \ 
    cd netcdf4-python && \ 
    cp setup.cfg.template setup.cfg && \ 
    python setup.py build && \ 
    python setup.py install && \
    cd .. && rm -rf netcdf4-python*

copy src/ /app/
run cd /app && python setup.py develop
expose 5000
cmd python -m odinapi.api
