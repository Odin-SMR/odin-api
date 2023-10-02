import pytest
import numpy as np
from odinapi.views.smr_quality import QualityControl


@pytest.fixture
def scan_target_sample_data():
    number_of_spectra = 10
    return {
        "stw": 7014775306 + 64 * np.arange(0, number_of_spectra),
        "tspill": 6.0 * np.ones(number_of_spectra),
        "tsys": 3700.0 * np.ones(number_of_spectra),
        "inttime": 1.85 * np.ones(number_of_spectra),
        "efftime": 2.4 * np.ones(number_of_spectra),
        "spectrum": 200 * np.ones(shape=(number_of_spectra, 112 * 8)),
        "altitude": 85e3 - 5e3 * np.arange(0, number_of_spectra),
        "type": 8 * np.ones(number_of_spectra, dtype="int"),
        "skybeamhit": 0 * np.ones(number_of_spectra, dtype="int"),
        "quality": 0 * np.ones(number_of_spectra),
        "frequency": {
            "SubBandIndex": [
                list(range(0, 112 * 8, 112)),
                list(range(111, 112 * 8, 112)),
            ]
        },
    }


@pytest.fixture
def scan_reference_sample_data():
    number_of_references = 11
    return {
        "stw": 7014775274 + 64 * np.arange(0, number_of_references),
        "inttime": 1.85 * np.ones(number_of_references),
        "sig_type": np.array(number_of_references * ["REF"]),
        "mech_type": np.array(number_of_references * ["SK1"]),
        "skybeamhit": 0 * np.ones(number_of_references, dtype="int"),
        "cc": np.ones(shape=(number_of_references, 8)),
    }


@pytest.fixture
def quality_control(scan_target_sample_data, scan_reference_sample_data):
    return QualityControl(scan_target_sample_data, scan_reference_sample_data)


class TestQualityControl:
    def test_check_tspill_is_ok(self, quality_control):
        quality_control.check_tspill()
        assert np.all(quality_control.quality == 0)

    def test_check_tspill_is_not_ok(self, quality_control):
        quality_control.specdata["tspill"][0] = 30.0
        quality_control.check_tspill()
        assert np.all(quality_control.quality == 0x0001)

    def test_check_trec_is_ok(self, quality_control):
        quality_control.check_trec()
        assert np.all(quality_control.quality == 0)

    def test_check_trec_is_not_ok(self, quality_control):
        quality_control.specdata["tsys"][2] = 12000.0
        quality_control.check_trec()
        assert np.all(quality_control.quality == 0x0002)

    def test_check_noise_is_ok(self, quality_control):
        quality_control.check_noise()
        assert np.all(quality_control.quality == 0)

    def test_check_noise_is_not_ok(self, quality_control):
        quality_control.specdata["tsys"][2] = 12000.0
        quality_control.check_noise()
        assert np.all(quality_control.quality == 0x0004)

    def test_check_scan_is_ok(self, quality_control):
        quality_control.check_scan()
        assert np.all(quality_control.quality == 0)

    def test_check_scan_is_not_ok(self, quality_control):
        quality_control.specdata["altitude"][5] = 100e3
        quality_control.check_scan()
        assert np.all(quality_control.quality == 0x0008)

    def test_check_nr_of_spectra_is_ok(self, quality_control):
        quality_control.check_nr_of_spec()
        assert np.all(quality_control.quality == 0)

    def test_check_nr_of_spectra_is_not_ok(self, quality_control):
        quality_control.specdata["type"] = 8 * np.ones(3)
        quality_control.check_nr_of_spec()
        assert np.all(quality_control.quality == 0x0010)

    def test_check_tb_is_ok(self, quality_control):
        quality_control.check_tb()
        assert np.all(quality_control.quality == 0)

    def test_check_tb_is_not_ok(self, quality_control):
        quality_control.specdata["spectrum"][5] = (
            300 + quality_control.specdata["spectrum"][5]
        )
        quality_control.check_tb()
        assert quality_control.quality[0::5].tolist() == [0, 0x0020]

    def test_check_integration_time_is_ok(self, quality_control):
        quality_control.check_int()
        assert np.all(quality_control.quality == 0)

    def test_check_integration_time_is_not_ok(self, quality_control):
        quality_control.specdata["inttime"][5] = 1.87
        quality_control.check_int()
        assert quality_control.quality[0::5].tolist() == [0, 0x0040]

    def test_check_observation_sequence_is_ok(self, quality_control):
        quality_control.check_obs_sequence()
        assert np.all(quality_control.quality == 0)

    def test_check_observation_sequence_is_not_ok(self, quality_control):
        quality_control.refdata["mech_type"][5] = "SK2"
        quality_control.check_obs_sequence()
        assert quality_control.quality[3:8].tolist() == [0, 0x0080, 0x0080, 0x0080, 0]

    def test_check_reference_integration_time_is_ok(self, quality_control):
        quality_control.check_ref_inttime()
        assert np.all(quality_control.quality == 0)

    def test_check_reference_integration_time_is_not_ok(self, quality_control):
        quality_control.refdata["inttime"][5] = 2.87
        quality_control.check_ref_inttime()
        assert quality_control.quality[3:7].tolist() == [0, 0x0100, 0x0100, 0]

    def test_check_moon_in_mainbeam_is_ok(self, quality_control):
        quality_control.check_moon_in_mainbeam()
        assert np.all(quality_control.quality == 0)

    def test_check_moon_in_mainbeam_is_not_ok(self, quality_control):
        quality_control.specdata["skybeamhit"][5] = 0x0200
        quality_control.check_moon_in_mainbeam()
        assert quality_control.quality[0::5].tolist() == [0, 0x0200]
