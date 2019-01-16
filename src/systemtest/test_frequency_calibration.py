import pytest
import numpy as np
from pg import DB
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
    fit_scan_median_spectrum,
    identify_species_by_lines
)


class DatabaseConnector(DB):
    def __init__(self, host, port):
        DB.__init__(self, dbname='odin', user='odinop', host=host, port=port)


@pytest.fixture
def scan_sample_data(odin_postgresql):
    backend = 'AC2'
    freqmode = 22
    scanid = 7016113563
    db_connection = DatabaseConnector(*odin_postgresql)
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
        'frequency_grids': np.tile(
            frequency_grid, (spectra.shape[0] - 2, 1)
        ),
        'spectra': spectra[2::, channels_id],
        'altitudes':
            scan_data_exporter.spectra['altitude'][2::]}


@pytest.fixture
def freq_corr_572(scan_sample_data):
    return Freqcorr572(
        scan_sample_data['frequency_grids'],
        scan_sample_data['spectra'],
        scan_sample_data['altitudes'])


class TestFreqcorr572():

    def test_altitude_check(self, odinapi_service, freq_corr_572):
        assert freq_corr_572.altitude_check() == 1

    def test_get_initial_fit_values(self, odinapi_service, freq_corr_572):
        [initial_guess_is_ok, f_initial, tb_initial] = \
            freq_corr_572.get_initial_fit_values()
        assert np.all([
            initial_guess_is_ok,
            f_initial,
            tb_initial] == [
                1,
                pytest.approx(576.5938, abs=1e-3),
                pytest.approx(82.1877, abs=1e-3)])

    def test_fit_data(self, odinapi_service, freq_corr_572):
        freq_corr_572.get_initial_fit_values()
        [fit_is_ok, freq1, freq2, _, _] = fit_scan_median_spectrum(
            576.5938,
            82.1877,
            freq_corr_572.frequency_grid,
            freq_corr_572.median_tb
        )
        assert np.all([
            fit_is_ok,
            freq1,
            freq2] == [
                True,
                pytest.approx(576.5938, abs=1e-3),
                pytest.approx(576.840, abs=1e-3)])

    def test_get_tb_profile(self, odinapi_service, freq_corr_572):
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

    def test_identify_species_by_profile(self, odinapi_service, freq_corr_572):
        tb_profile = freq_corr_572.get_tb_profile(
            576.593, 576.840)
        co_found = freq_corr_572.identify_species_by_profile(
            tb_profile)
        assert co_found

    def test_identify_species_by_lines(self, odinapi_service, freq_corr_572):
        freq_corr_572.get_initial_fit_values()
        [fit_is_ok, _, _, amplitude_1, amplitude_2] = (
            fit_scan_median_spectrum(
                82.1877,
                576.5938,
                freq_corr_572.frequency_grid,
                freq_corr_572.median_tb
            )
        )
        co_found = identify_species_by_lines(
            amplitude_1, amplitude_2)
        assert co_found

    def test_get_frequency_offset_of_scan(
        self, odinapi_service, freq_corr_572,
    ):
        (scan_correction_is_ok, frequency_offset) = (
            freq_corr_572.get_frequency_offset_of_scan()
        )
        assert np.all([
            scan_correction_is_ok,
            frequency_offset] == [
                True,
                pytest.approx(0.3254, abs=1e-4)])

    def test_run_frequency_correction(self, odinapi_service, freq_corr_572):
        (
            scan_correction_is_ok,
            single_spectrum_correction_is_ok,
            frequency_offset_of_scan,
            frequencies_offset_per_spectrum
        ) = freq_corr_572.run_frequency_correction()
        assert np.all([
            scan_correction_is_ok,
            frequency_offset_of_scan,
            ] == [
                True,
                pytest.approx(0.3254, abs=1e-4)])
        assert np.all(single_spectrum_correction_is_ok)
        assert np.max(
            np.abs(frequencies_offset_per_spectrum)) < 5e-3
