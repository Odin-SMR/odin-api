from pathlib import Path
import pytest

from odinapi.views.read_mipas import read_mipas_file

from .partiallistmatch import PartialListMatch


@pytest.fixture
def mipas_basepath_pattern():
    p = Path(__file__)
    for p in p.parents:
        if p.name == 'src':
            p = p.parent
            break
    return p / 'data' / 'vds-data' / 'Envisat_MIPAS_Level2' / '{0}' / 'V5'


def test_read_mipas_file(mipas_basepath_pattern):
    data = read_mipas_file(
        'MIPAS-E_IMK.200702.V5R_O3_224.nc',
        '2007-02-01',
        'O3',
        2,
        basepath_pattern=str(mipas_basepath_pattern)
    )
    expect = {
        'MJD': 54132.00168981482,
        'akm_diagonal': PartialListMatch(
            60,
            [0.0, -0.008270449936389923, 0.06216210126876831],
            startidx=5,
            name='akm_diagonal',
        ),
        'altitude': PartialListMatch(60, [0.0, 4.0, 5.0], name='altitude'),
        'chi2': 2.436000108718872,
        'dof': 20.0,
        'eta': PartialListMatch(
            27, [11.432100296020508, 12.850199699401855], name='eta',
        ),
        'eta_indices': list(range(1, 28)),
        'geo_id': '25736_20070201T000226Z',
        'latitude': -7.782657623291016,
        'longitude': -26.594581604003906,
        'los': PartialListMatch(
            27, [12.368152618408203, 13.724454879760742], name='los',
        ),
        'pressure': PartialListMatch(
            60, [1002.919677734375, 626.6535034179688], name='pressure',
        ),
        'rms': 19.3700008392334,
        'sub_id': '1822',
        'sza': 141.66810607910156,
        'target': PartialListMatch(
            60, [0.12195233255624771, 0.13413915038108826], startidx=6,
            name='target',
        ),
        'target_noise_error': PartialListMatch(
            60,
            [0.04682280123233795, 0.04682280123233795, 0.039234600961208344],
            startidx=5,
            name='target_noise_error',
        ),
        'temperature': PartialListMatch(
            60,
            [300.2716064453125, 278.47161865234375],
            name='temperature'
        ),
        'time': 13545.001689814962,
        'visibility': PartialListMatch(
            60, [0] * 8 + [1, 1], name='visibility',
        ),
        'vr_akdiag': PartialListMatch(
            60, [120., 16.086973190307617], startidx=6, name='vr_akdiag',
        ),
        'vr_col': PartialListMatch(
            60, [0., 0.9611631035804749], startidx=5, name='vr_col',
        ),
        'vr_row': PartialListMatch(
            60, [1.2473870515823364, 1.2383352518081665], startidx=6,
            name='vr_row',
        ),
    }

    assert data == expect
