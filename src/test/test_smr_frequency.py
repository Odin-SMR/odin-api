# pylint: skip-file
import pytest
import numpy as np
from odinapi.views.smr_frequency import (
    Smrl1bFreqspec,
    Smrl1bFreqsort,
    get_bad_ssb_modules,
    doppler_corr,
)


@pytest.fixture
def scan_data_sample():
    number_of_spectra = 10
    return {
        'backend': 1 * np.ones(
            number_of_spectra, dtype='int'),
        'channels': 896 * np.ones(
            number_of_spectra, dtype='int'),
        'mode': 127 * np.ones(
            number_of_spectra, dtype='int'),
        'ssb_fq': 1e6 * np.repeat(
            [[4300, 3700, 4100, 3900]],
            number_of_spectra,
            axis=0),
        'freqres': 1000000.0 * np.ones(
            number_of_spectra),
        'skyfreq': 544.615e9 * np.ones(
            number_of_spectra),
        'restfreq': 544.603e9 * np.ones(
            number_of_spectra),
        'lofreq': 548.515e9 * np.ones(
            number_of_spectra),
        'spectra': 100.0 * np.ones(
            shape=(number_of_spectra, 896))}


@pytest.fixture
def frequency_grid(scan_data_sample):
    smr_freq_spec = Smrl1bFreqspec()
    return smr_freq_spec.get_frequency(
            scan_data_sample, 1)


class TestSmrl1bFreqspec():

    def test_get_frequency(self, frequency_grid):
        assert frequency_grid.shape == (8, 112)
        assert(
            np.all(frequency_grid[0: 8, 0] == [
                pytest.approx(544.203e9, abs=1e5),
                pytest.approx(544.203e9, abs=1e5),
                pytest.approx(544.803e9, abs=1e5),
                pytest.approx(544.803e9, abs=1e5),
                pytest.approx(544.403e9, abs=1e5),
                pytest.approx(544.403e9, abs=1e5),
                pytest.approx(544.603e9, abs=1e5),
                pytest.approx(544.603e9, abs=1e5)]))

    def test_get_seq_pattern_standard(self, scan_data_sample):
        smr_freq_spec = Smrl1bFreqspec()
        smr_freq_spec.get_frequency(scan_data_sample, 1)
        sequence_pattern = smr_freq_spec.get_seq_pattern()
        expected_sequence_pattern = np.array([
            1, 1, 1, -1, 1, 1, 1, -1,
            1, -1, 1, 1, 1, -1, 1, 1])
        assert np.all(
            sequence_pattern == expected_sequence_pattern)

    def test_get_seq_pattern_mode17(self, scan_data_sample):
        scan_data_sample['mode'] = 17 * scan_data_sample['mode'] / 127
        smr_freq_spec = Smrl1bFreqspec()
        smr_freq_spec.get_frequency(scan_data_sample, 1)
        sequence_pattern = smr_freq_spec.get_seq_pattern()
        expected_sequence_pattern = np.array([
            1,  1,  4, -1,  0,  0,  0, 0,
            0,  0,  3,  1,  0,  0,  0,  0
        ])
        assert np.all(
            sequence_pattern == expected_sequence_pattern)

    def test_get_seq_pattern_mode0(self, scan_data_sample):
        scan_data_sample['mode'] = 0 * scan_data_sample['mode'] / 127
        smr_freq_spec = Smrl1bFreqspec()
        smr_freq_spec.get_frequency(scan_data_sample, 1)
        sequence_pattern = smr_freq_spec.get_seq_pattern()
        expected_sequence_pattern = np.array([
            8, 1, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0
        ])
        assert np.all(
            sequence_pattern == expected_sequence_pattern)


class TestSmrl1bFreqsort():

    def test_get_sorted_ac_spectrum(
            self, scan_data_sample, frequency_grid):
        bad_modules = np.mean(frequency_grid, 1)[0: 2]
        frequency_grid = frequency_grid.flatten()
        smr_freq_sort = Smrl1bFreqsort()
        (
            freqvec,
            tempspec,
            ssb_index_in_spectrum,
            channels_id
        ) = (
            smr_freq_sort.get_sorted_ac_spectrum(
                frequency_grid,
                scan_data_sample['spectra'][3],
                bad_modules,
            )
        )
        assert freqvec[0] == pytest.approx(
            544.403e9 - 110e6, abs=1e5)
        assert freqvec[-1] == pytest.approx(
            544.803e9 + 110e6, abs=1e5)
        assert freqvec.shape == tempspec.shape
        expected_ssb = [
            1, -1, -1,
            2, -1, -1,
            3, 409, 508,
            4, 509, 618,
            5, 111, 210,
            6, 1, 110,
            7, 310, 408,
            8, 211, 309,
            ]
        assert(
            ssb_index_in_spectrum == expected_ssb)
        assert channels_id.shape[0] == 618
        assert channels_id[0] == 670
        assert channels_id[-1] == 446

    def test_ac_filter(
            self, scan_data_sample, frequency_grid):
        bad_modules = np.mean(frequency_grid, 1)[0: 2]
        smr_freq_sort = Smrl1bFreqsort()
        smr_freq_sort.freq = frequency_grid.flatten()
        smr_freq_sort.ydata = scan_data_sample['spectra'][0]
        smr_freq_sort.ac_filter(bad_modules)
        assert smr_freq_sort.freq.shape[0] == 110 * 6
        assert (
            set(smr_freq_sort.ssb_ind) ==
            set([3, 4, 5, 6, 7, 8]))
        assert smr_freq_sort.channels_id[0] == 225
        assert smr_freq_sort.channels_id[-1] == 894

    def test_sort_from_middle(
            self, scan_data_sample, frequency_grid):
        smr_freq_sort = Smrl1bFreqsort()
        smr_freq_sort.freq = frequency_grid.flatten()
        smr_freq_sort.ydata = scan_data_sample['spectra'][0]
        smr_freq_sort.ac_filter([])
        smr_freq_sort.sort_from_middle(
            frequency_grid.flatten())
        assert smr_freq_sort.ssb_ind.shape[0] == 817
        assert np.all(
            smr_freq_sort.ssb_ind[0: 110] == 1)
        assert np.all(
            smr_freq_sort.ssb_ind[111: 111 + 99] == 2)
        assert np.all(
            smr_freq_sort.ssb_ind[210: 210 + 100] == 3)
        assert np.all(
            smr_freq_sort.ssb_ind[310: 310 + 110] == 4)
        assert np.all(
            smr_freq_sort.ssb_ind[420: 420 + 100] == 5)
        assert np.all(
            smr_freq_sort.ssb_ind[520: 520 + 99] == 6)
        assert np.all(
            smr_freq_sort.ssb_ind[619: 619 + 99] == 7)
        assert np.all(
            smr_freq_sort.ssb_ind[718: 718 + 99] == 8)


def test_get_bad_ssb_modules_for_ac1(
        scan_data_sample, frequency_grid):
    backend = 1
    bad_modules = get_bad_ssb_modules(
        backend,
        scan_data_sample['spectra'],
        frequency_grid)
    assert np.all(
        bad_modules ==
        np.mean(frequency_grid, 1)[0: 2])


def test_get_bad_ssb_modules_for_ac2(
        scan_data_sample, frequency_grid):
    backend = 2
    bad_modules = get_bad_ssb_modules(
        backend,
        scan_data_sample['spectra'],
        frequency_grid)
    assert bad_modules == np.mean(frequency_grid, 1)[2]


def test_get_bad_ssb_modules_for_dead_band(
        scan_data_sample, frequency_grid):
    backend = 1
    scan_data_sample[
        'spectra'][3][112 * 2: 112 * 3] = 0
    bad_modules = get_bad_ssb_modules(
        backend,
        scan_data_sample['spectra'],
        frequency_grid)
    assert np.all(
        bad_modules ==
        np.mean(frequency_grid, 1)[0: 3])


def test_doppler_corr(
        scan_data_sample, frequency_grid):
    (
        lofreq_corrected,
        frequency_grid_corrected,
        ) = doppler_corr(
        scan_data_sample['skyfreq'][0],
        scan_data_sample['restfreq'][0],
        scan_data_sample['lofreq'][0],
        frequency_grid)
    assert np.all(
            [
                lofreq_corrected,
                frequency_grid_corrected[0, 0]] ==
            [
                pytest.approx(548.503e9, abs=1e5),
                pytest.approx(
                    -scan_data_sample['ssb_fq'][0][0],
                    abs=1e5)])
