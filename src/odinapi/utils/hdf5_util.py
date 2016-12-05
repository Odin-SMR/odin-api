"""
Provide context managers for opening hd5 and netCDF4 files.

The hdf5 c library is not thread safe, so these context managers use a thread
lock to ensure that only one file is open at the same time.

There is a flag that can be used to build the hdf5 library thread safe,
but that does not work together with h5py.

From https://support.hdfgroup.org/hdf5-quest.html#gconc :

    Users are often surprised to learn that (1) concurrent access to different
    datasets in a single HDF5 file and (2) concurrent access to different HDF5
    files both require a thread-safe version of the HDF5 library.

See also this link for info about --disable-hl:

    https://support.hdfgroup.org/ftp/HDF5/releases/ReleaseFiles/hdf5-1.8.16-RELEASE.txt

    ./configure --enable-threadsafe --disable-hl

But h5py uses the high level library: https://github.com/h5py/h5py/issues/741

This error occurs when hdf5 is built with the threadsafe and disable hl flag:

    >>> fname = '/vds-data/ACE_Level2/v2/2004-03/ss2969.nc'
    >>> import h5py
    >>> from netCDF4 import Dataset
    >>> f = Dataset(fname, 'r')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "netCDF4/_netCDF4.pyx", line 1811,
          in netCDF4._netCDF4.Dataset.__init__ (netCDF4/_netCDF4.c:13221)
    IOError: NetCDF: HDF error
"""
from contextlib import contextmanager
from threading import Lock

import h5py
import netCDF4

HDF5_LOCK = Lock()


@contextmanager
def thread_safe_h5py_file(path, mode='r'):

    with HDF5_LOCK:
        f = h5py.File(path, mode)
        yield f
        f.close()


@contextmanager
def thread_safe_netcdf4_dataset(path, mode='r'):

    with HDF5_LOCK:
        f = netCDF4.Dataset(path, mode)
        yield f
        f.close()
