"""
Script for adding level2 processing jobs to job service
"""
from sys import exit

import requests

from odinapi.utils.encrypt_util import encode_level2_target_parameter


def make_job_data(scanid, freqmode, odin_api_root):
    return {
        'id': str(scanid),
        'type': 'qsmr',
        'source_url': odin_api_root + '/v4/l1_log/{freqmode}/{scanid}/'.format(
            scanid=scanid, freqmode=freqmode),
        'target_url': odin_api_root + '/v4/level2?d={}'.format(
            encode_level2_target_parameter(scanid, freqmode))
    }


def add_job(scanid, freqmode, project, odin_api_root, job_api_root,
            job_api_user, job_api_password):
    job = make_job_data(scanid, freqmode, odin_api_root)
    requests.post(
        job_api_root + '/v4/{}/jobs'.format(project),
        headers={'Content-Type': "application/json"},
        json=job, auth=(job_api_user, job_api_password)
    )


def add_jobs(scanids, freqmode, project, odin_api_root, job_api_root,
             job_api_user, job_api_password):
    for i, scanid in enumerate(scanids):
        add_job(scanid, freqmode, project, odin_api_root, job_api_root,
                job_api_user, job_api_password)
        if i and not i % 100:
            print('%d jobs added' % i)


def add_jobs_from_file(filename, freqmode, project, odin_api_root,
                       job_api_root, job_api_user, job_api_password):
    raise NotImplementedError


def main(args=None):
    # TODO: argparser
    raise NotImplementedError

if __name__ == '__main__':
    exit(main())
