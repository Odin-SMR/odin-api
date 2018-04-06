# pylint: skip-file
import pytest
import numpy as np
from pg import DB
from odinapi.test.testdefs import system
from odinapi.views.level1b_scandata_exporter_v2 import (
    ScandataExporter,
    smr_lofreqcorr,
    unsplit_normalmode,
    apply_calibration_step2,
)
from odinapi.views.smr_frequency import (
    Smrl1bFreqspec,
    Smrl1bFreqsort,
    get_bad_ssb_modules,
)
from odinapi.views.freq_calibration import (
    Freqcorr572,
)


class DatabaseConnector(DB):
    def __init__(self):
        DB.__init__(
            self,
            dbname='odin',
            user='odinop',
            host='localhost',
        )


@pytest.fixture
def scan_sample_data():
    backend = 'AC2'
    freqmode = 22
    scanid = 7016113563
    db_connection = DatabaseConnector()
    scan_data_exporter = ScandataExporter(
        backend, db_connection)
    scan_data_exporter.get_db_data(
        freqmode, scanid)
    scan_data_exporter.decode_specdata()
    assert len(scan_data_exporter.spectra['stw']) == 94
    scan_data_exporter = apply_calibration_step2(
        db_connection, scan_data_exporter)
    scan_data_exporter = unsplit_normalmode(
        scan_data_exporter)
    assert len(scan_data_exporter.spectra['stw']) == 47
    smr_lofreqcorr(scan_data_exporter)
    smr_freq_spec = Smrl1bFreqspec()
    smr_freq_sort = Smrl1bFreqsort()
    frequency_grid = smr_freq_spec.get_frequency(
        scan_data_exporter.spectra, 0)
    spectra = np.array(
        scan_data_exporter.spectra['spectrum'])
    bad_modules = get_bad_ssb_modules(
        scan_data_exporter.spectra['backend'][0],
        spectra,
        frequency_grid,
        False)
    frequency_grid = frequency_grid.flatten()
    frequency_grid, _, _, channels_id = (
        smr_freq_sort.get_sorted_ac_spectrum(
            frequency_grid,
            spectra[0],
            bad_modules))
    return {
        'frequency_grid': frequency_grid,
        'spectra': spectra[2::, channels_id],
        'altitudes':
            scan_data_exporter.spectra['altitude'][2::]}


@pytest.fixture
def freq_corr_572(scan_sample_data):
    return Freqcorr572(
        scan_sample_data['frequency_grid'],
        scan_sample_data['spectra'],
        scan_sample_data['altitudes'])


@system
@pytest.mark.usefixtures('dockercompose')
class TestFreqcorr572():

    def test_altitude_check(self, freq_corr_572):
        assert freq_corr_572.altitude_check() == 1

    def test_get_initial_fit_values(self, freq_corr_572):
        [initial_guess_is_ok, f_initial, tb_initial] = \
            freq_corr_572.get_initial_fit_values()
        assert np.all([
            initial_guess_is_ok,
            f_initial,
            tb_initial] == [
                1,
                pytest.approx(576.5938, abs=1e-3),
                pytest.approx(82.1877, abs=1e-3)])

    def test_fit_data(self, freq_corr_572):
        freq_corr_572.get_initial_fit_values()
        [fit_is_ok, freq1, freq2] = freq_corr_572.fit_data(
            82.1877, 576.5938)
        assert np.all([
            fit_is_ok,
            freq1,
            freq2] == [
                1,
                pytest.approx(576.5938, abs=1e-3),
                pytest.approx(576.840, abs=1e-3)])

    def test_get_tb_profile(self, freq_corr_572):
        tb_profiles = freq_corr_572.get_tb_profile(
            576.593, 576.840)
        assert tb_profiles.shape == (45, 2)
        assert np.all([
            tb_profiles[0, 0],
            tb_profiles[44, 0],
            tb_profiles[0, 1],
            tb_profiles[44, 1]] == [
                pytest.approx(-2.2, abs=1e-1),
                pytest.approx(198.3, abs=1e-1),
                pytest.approx(-7.0, abs=1e-1),
                pytest.approx(195.6, abs=1e-1)])

    def test_identify_species_by_profile(self, freq_corr_572):
        tb_profile = freq_corr_572.get_tb_profile(
            576.593, 576.840)
        co_found = freq_corr_572.identify_species_by_profile(
            tb_profile)
        assert co_found == 1

    def test_identify_species_by_lines(self, freq_corr_572):
        [initial_guess_is_ok, f_initial, tb_initial] = \
            freq_corr_572.get_initial_fit_values()
        [fit_is_ok, freq1, freq2] = freq_corr_572.fit_data(
                tb_initial, f_initial)
        co_found = freq_corr_572.identify_species_by_lines()
        assert co_found == 1

    def test_run_freq_corr(self, freq_corr_572):
        freq_corr_572.run_freq_corr()
        assert np.all([
            freq_corr_572.correction_is_ok,
            freq_corr_572.fdiff] == [
                1,
                pytest.approx(0.3254, abs=1e-4)])
