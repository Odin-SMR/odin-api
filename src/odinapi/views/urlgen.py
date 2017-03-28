"""Provide functions for generation of API urls"""


def get_freqmode_info_url(root_url, version, date, backend, freqmode):
    if version in {'v4'}:
        return '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/'.format(
            root_url, version, date, backend, freqmode)
    else:
        return '{0}rest_api/{1}/freqmode_info/{2}/{3}/'.format(
            root_url, version, date, freqmode)


def get_freqmode_raw_url(root_url, version, date, backend, freqmode):
    if version in {'v4'}:
        return '{0}rest_api/{1}/freqmode_raw/{2}/{3}/{4}/'.format(
            root_url, version, date, backend, freqmode)
    else:
        return '{0}rest_api/{1}/freqmode_raw/{2}/{3}/'.format(
            root_url, version, date, freqmode)
