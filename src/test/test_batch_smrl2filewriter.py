import os
import datetime as dt
from unittest.mock import call, patch, ANY

import pytest  # type: ignore

from odinapi.utils import batch_smrl2filewriter


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "fixtures", "odinl2.json"
)


@pytest.mark.parametrize("index,expect", (
    (
        0,
        batch_smrl2filewriter.ProductConf(
            project="ALL-Strat-v3.0.0",
            product="ClO / 501 GHz / 20 to 55 km",
            freqmode=1,
            start=dt.datetime(2002, 1, 1),
            end=dt.datetime(2002, 12, 31),
            outdir="ALL-Strat-v3.0.0",
            product_label="ClO / FM1 / 501 GHz / 20 to 55 km",
        ),
    ),
    (
        13,
        batch_smrl2filewriter.ProductConf(
            project="ALL19lowTunc",
            product="Temperature - 557 (Fmode 19) - 45 to 90 km",
            freqmode=19,
            start=dt.datetime(2003, 1, 1),
            end=dt.datetime(2004, 12, 31),
            outdir="ALL-Meso-v3.0.0",
        ),
    ),
))
def test_load_config(index, expect):
    configs = batch_smrl2filewriter.load_config(CONFIG_FILE)
    assert configs[index] == expect


@pytest.mark.freeze_time('2017-05-21')
@pytest.mark.parametrize("end,expect", (
    (None, dt.datetime(2017, 1, 31)),
    ("2006-01-01", dt.datetime(2006, 1, 1)),
))
def test_set_end(end, expect):
    assert batch_smrl2filewriter.set_end(end) == expect


@patch('odinapi.utils.smrl2filewriter.cli', return_value=None)
def test_cli(patched_smrl2filewriter_cli):
    batch_smrl2filewriter.cli(
        [CONFIG_FILE, "savedir"]
    )
    patched_smrl2filewriter_cli.assert_has_calls([
        call([
            'ALL-Strat-v3.0.0',
            'ClO / 501 GHz / 20 to 55 km',
            '1',
            '2002-01-01',
            '2002-12-31',
            '-p',
            'ClO / FM1 / 501 GHz / 20 to 55 km',
            '-q',
            'savedir/ALL-Strat-v3.0.0',
        ]),
        ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY,
        call([
            'ALL19lowTunc',
            'Temperature - 557 (Fmode 19) - 45 to 90 km',
            '19',
            '2003-01-01',
            '2004-12-31',
            '-p',
            None,
            '-q',
            'savedir/ALL-Meso-v3.0.0',
        ])
    ])
