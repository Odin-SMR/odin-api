""" Odin-API """
from setuptools import setup

setup(
    name='Odin-API',
    version='1.0',
    long_description=__doc__,
    entry_points={"console_scripts": [
            "populate_cache_table = scripts.populate_cache_table:cli",
            "populate_vds_table = scripts.populate_vds_table:cli",
            "processsolar = scripts.processsolar:processsolar",
            ]},
    packages=['odinapi', 'odinapi.views', 'scripts'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)
