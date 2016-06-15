""" Odin-API """
from setuptools import setup

setup(
    name='Odin-API',
    version='1.0',
    long_description=__doc__,
    entry_points= {"console_scripts": [
            "populate_cache_table = src.scripts.populate_cache_table:cli",
            "populate_vds_table = src.scripts.populate_vds_table:cli",
            "processsolar = src.scripts.processsolar:processsolar",
            ]},
    packages=['odinapi','odinapi.views'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)
