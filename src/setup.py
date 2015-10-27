""" Odin-API """
from setuptools import setup

setup(
    name='Odin-API',
    version='1.0',
    long_description=__doc__,
    packages=['odinapi','odinapi.views'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)
