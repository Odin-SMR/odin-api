"""frequency correction tools for odin-api
"""
import numpy as np
from scipy.optimize import curve_fit  # type: ignore


CO_TRUE = 576.268  # CO line center frequency [GHz]
LINE_POSITION_DIFFERENCE_CO_O3 = 0.247  # freq. diff. CO and O3 line [GHz]
FREQUENCY_LIMIT_LOWER = 576.263  # frequency limits for single
FREQUENCY_LIMIT_UPPER = 576.273  # spectrum correction [GHz]


class Freqcorr572:
    """A class derived for performing frequency
    calibration of data from Odin/SMR 572 frontend
    """

    def __init__(self, frequency_grids, spectra, altitude):
        self.frequency_grids = np.array(frequency_grids)
        self.spectra = np.array(spectra)
        self.altitude = np.array(altitude, dtype=float)
        self.frequency_grid = self.get_frequency_grid_in_middle_of_scan()
        self.median_tb = np.zeros_like(self.frequency_grid)

    def altitude_check(self):
        """check that scan covering 40 to 60 km in altitude"""
        return np.min(self.altitude) < 40e3 and np.max(self.altitude) > 60e3

    def get_frequency_grid_in_middle_of_scan(self):
        """get the frequency grid for spectrum with tangent altitude
        around 50 km
        """
        return self.frequency_grids[np.argsort(np.abs(self.altitude - 50e3))[0]]

    def get_initial_fit_values(self, tbmin=10):
        """identify frequency and Tb of the line with
        lowest frequency in median spectra of scan,
        these values will be used as starting values
        for a more detailed fit
        """
        high_altitude_index = np.nonzero(self.altitude > 20e3)[0]
        if self.altitude_check():
            # median is preferable to use
            self.median_tb = np.median(self.spectra[high_altitude_index], 0)
        else:
            # if we do not have much measurements from
            # low altitude we must use mean instead of median,
            # because taking the median can resulting in
            # that all lines are removed from spectra
            self.median_tb = np.mean(self.spectra[high_altitude_index], 0)
        high_tb_index = np.nonzero(self.median_tb > tbmin)[0]
        if high_tb_index.shape[0] < 2:
            frequency_initial_guess = None
            tb_initial_guess = None
            initial_guess_is_ok = False
        else:
            tb_initial_guess = np.max(
                self.median_tb[
                    np.nonzero(
                        self.frequency_grid
                        <= self.frequency_grid[high_tb_index][0] + 100e6
                    )[0]
                ]
            )
            frequency_initial_guess = (
                self.frequency_grid[np.nonzero(self.median_tb == tb_initial_guess)[0]][
                    0
                ]
                / 1e9
            )
            initial_guess_is_ok = True
        return (initial_guess_is_ok, frequency_initial_guess, tb_initial_guess)

    def get_tb_profile(self, freq1, freq2):
        """extract tb as function of altitude for the estimated
        line center frequencies. This data will be used to
        identify species
        """
        tb_profile = []
        for spectrum in self.spectra:
            if (freq1 > self.frequency_grid[0] / 1e9) and (
                freq2 < self.frequency_grid[-1] / 1e9
            ):
                tbi = np.interp([freq1, freq2], self.frequency_grid / 1e9, spectrum)
                tb_profile.append([tbi[0], tbi[1]])
            elif freq1 > self.frequency_grid[0] / 1e9:
                tbi = np.interp([freq1], self.frequency_grid / 1e9, spectrum)
                tb_profile.append([tbi[0], np.nan])
            elif freq2 < self.frequency_grid[-1] / 1e9:
                tbi = np.interp([freq1], self.frequency_grid / 1e9, spectrum)
                tb_profile.append([np.nan, tbi[0]])
            else:
                tb_profile.append([np.nan, np.nan])
        return np.array(tb_profile)

    def identify_species_by_profile(self, tb_profile, zmin=40, zmax=60, cutoff=-0.0045):
        """identify species from the change (between 40 and 60 km)
        in tb profile and derive the frequency correction to apply
        """
        if self.altitude[0] > self.altitude[-1]:
            tb_diff = np.interp(
                [zmin, zmax], self.altitude[-1::-1] / 1e3, tb_profile[-1::-1, 0]
            )
        else:
            tb_diff = np.interp([zmin, zmax], self.altitude / 1e3, tb_profile[:, 0])
        tbchange = (tb_diff[1] - tb_diff[0]) / 20e3
        return tbchange > cutoff

    def get_initial_fit_values_single_spectrum_correction(self, index_of_spectrum):
        """get initial fit values, i.e maximum brightness temperature
        and corresponding frequency within given frequency limits around
        the CO line
        """
        index_within_frequency_limits = np.nonzero(
            (self.frequency_grids[index_of_spectrum] / 1e9 > FREQUENCY_LIMIT_LOWER)
            & (self.frequency_grids[index_of_spectrum] / 1e9 < FREQUENCY_LIMIT_UPPER)
        )[0]
        if index_within_frequency_limits.shape[0] > 0:
            index_greatest_tb = self.spectra[index_of_spectrum][
                index_within_frequency_limits
            ].argmax()

            frequency_initial_guess = (
                self.frequency_grids[index_of_spectrum][
                    index_within_frequency_limits[index_greatest_tb]
                ]
                / 1e9
            )

            tb_initial_guess = self.spectra[index_of_spectrum][
                index_within_frequency_limits
            ].max()
        else:
            frequency_initial_guess = None
            tb_initial_guess = None
        return (frequency_initial_guess, tb_initial_guess)

    def get_frequency_offset_of_each_spectrum_in_scan(self):
        """estimate frequency offset for each spectrum in scan"""
        frequencies_fitted = np.zeros_like(self.altitude)
        frequencies_offset = np.zeros_like(self.altitude)
        single_spectrum_correction_is_ok = np.full(
            self.altitude.shape[0], False, dtype=bool
        )

        for index_of_spectrum in range(0, self.altitude.shape[0]):
            (
                frequency_initial_guess,
                tb_initial_guess,
            ) = self.get_initial_fit_values_single_spectrum_correction(
                index_of_spectrum
            )
            if frequency_initial_guess is None or tb_initial_guess is None:
                continue
            try:
                frequencies_fitted[index_of_spectrum] = (
                    fit_single_altitude_spectrum(
                        frequency_initial_guess,
                        tb_initial_guess,
                        self.frequency_grids[index_of_spectrum],
                        self.spectra[index_of_spectrum],
                    )
                )[1]
            except RuntimeError:
                continue

            single_spectrum_correction_is_ok[index_of_spectrum] = True
            if (
                frequencies_fitted[index_of_spectrum] < FREQUENCY_LIMIT_LOWER
                or frequencies_fitted[index_of_spectrum] > FREQUENCY_LIMIT_UPPER
            ):
                frequencies_fitted[index_of_spectrum] = frequency_initial_guess

        frequencies_offset[single_spectrum_correction_is_ok] = (
            frequencies_fitted[single_spectrum_correction_is_ok] - CO_TRUE
        )
        return (single_spectrum_correction_is_ok, frequencies_offset)

    def co_is_found_in_fitted_data(
        self, frequency_co_line, frequency_o3_line, amplitude_co_line, amplitude_o3_line
    ):
        """check if CO signatures can be found in fitted data"""
        if self.altitude_check():
            # identify species from tb(ztan) gradient
            tb_profile = self.get_tb_profile(frequency_co_line, frequency_o3_line)
            co_found = self.identify_species_by_profile(tb_profile)
            if not co_found:
                co_found = identify_species_by_lines(
                    amplitude_co_line, amplitude_o3_line
                )
        else:
            # possibly identify species if two lines are observed
            co_found = identify_species_by_lines(amplitude_co_line, amplitude_o3_line)
        return co_found

    def get_frequency_offset_of_scan(self):
        """estimate a scalar frequency offset of scan"""
        (
            initial_guess_is_ok,
            frequency_initial_guess,
            tb_initial_guess,
        ) = self.get_initial_fit_values()
        scan_correction_is_ok = False
        frequency_offset_of_scan = 0
        if initial_guess_is_ok:
            (
                fit_is_ok,
                frequency_co_line,
                frequency_o3_line,
                amplitude_co_line,
                amplitude_o3_line,
            ) = fit_scan_median_spectrum(
                frequency_initial_guess,
                tb_initial_guess,
                self.frequency_grid,
                self.median_tb,
            )
            if fit_is_ok:
                if self.co_is_found_in_fitted_data(
                    frequency_co_line,
                    frequency_o3_line,
                    amplitude_co_line,
                    amplitude_o3_line,
                ):
                    frequency_offset_of_scan = frequency_co_line - CO_TRUE
                    scan_correction_is_ok = True

        return (scan_correction_is_ok, frequency_offset_of_scan)

    def run_frequency_correction(self):
        (
            scan_correction_is_ok,
            frequency_offset_of_scan,
        ) = self.get_frequency_offset_of_scan()
        if scan_correction_is_ok:
            self.frequency_grids = self.frequency_grids - (
                frequency_offset_of_scan * 1e9
            )

            (
                single_spectrum_correction_is_ok,
                frequencies_offset_per_spectrum,
            ) = self.get_frequency_offset_of_each_spectrum_in_scan()
        else:
            single_spectrum_correction_is_ok = np.full(
                self.altitude.shape[0], False, dtype=bool
            )
            frequencies_offset_per_spectrum = np.zeros_like(self.altitude)
        return (
            scan_correction_is_ok,
            single_spectrum_correction_is_ok,
            frequency_offset_of_scan,
            frequencies_offset_per_spectrum,
        )


def identify_species_by_lines(amplitude_co_line, amplitude_o3_line):
    """identify species by checking if two lines were found"""
    return amplitude_co_line > 10 and amplitude_o3_line > 10


def fit_function_scan_median_spectrum(
    frequency_grid,
    line_amplitude_co,
    line_position_co,
    line_width_co,
    line_amplitude_o3,
    line_width_o3,
):
    """fitting function for scan median spectum"""
    line_position_o3 = line_position_co + LINE_POSITION_DIFFERENCE_CO_O3
    return line_amplitude_co * np.exp(
        -(((frequency_grid - line_position_co) / line_width_co) ** 2)
    ) + line_amplitude_o3 * np.exp(
        -(((frequency_grid - line_position_o3) / line_width_o3) ** 2)
    )


def fit_function_single_altitude_spectrum(
    frequency_grid, line_amplitude, line_position, line_width, baseline
):
    """fitting function for single altitude spectrum"""
    return baseline + line_amplitude * np.exp(
        -(((frequency_grid - line_position) / line_width) ** 2)
    )


def fit_scan_median_spectrum(
    line_position_co, line_amplitude_co, frequency_grid, spectrum
):
    """try to fit data using derived initial fit values"""
    # default initial fitting parameters, value not crtitical
    line_width_co = 2e-3
    line_amplitude_o3 = 100
    line_width_o3 = 2e-2
    initial_guess = [
        line_amplitude_co,
        line_position_co,
        line_width_co,
        line_amplitude_o3,
        line_width_o3,
    ]
    try:
        popt, _ = curve_fit(
            fit_function_scan_median_spectrum,
            frequency_grid / 1e9,
            spectrum,
            p0=initial_guess,
            sigma=10 * np.ones_like(frequency_grid),
        )
        fitted_line_amplitude_co = popt[0]
        fitted_line_amplitude_o3 = popt[3]
        fitted_line_position_co = popt[1]
        fitted_line_position_o3 = popt[1] + LINE_POSITION_DIFFERENCE_CO_O3
        fit_is_ok = fit_scan_median_spectrum_is_valid(
            frequency_grid / 1e9, fitted_line_position_co
        )
    except RuntimeError:
        fitted_line_amplitude_co = None
        fitted_line_amplitude_o3 = None
        fitted_line_position_co = None
        fitted_line_position_o3 = None
        fit_is_ok = False
    return (
        fit_is_ok,
        fitted_line_position_co,
        fitted_line_position_o3,
        fitted_line_amplitude_co,
        fitted_line_amplitude_o3,
    )


def fit_scan_median_spectrum_is_valid(frequency_grid, fitted_line_position_co):
    """check that there are avaialable frequencies, both smaller and
    greater, in the frequency grid, close to the fitted frequency of the
    co line
    """
    maximum_frequency_difference = 0.0015  # GHz
    frequency_difference = frequency_grid - fitted_line_position_co
    return (
        np.min(frequency_difference[frequency_difference > 0])
        < maximum_frequency_difference
        and np.max(frequency_difference[frequency_difference < 0])
        > -maximum_frequency_difference
    )


def fit_single_altitude_spectrum(
    line_position, line_amplitude, frequency_grid, spectrum
):
    """try to fit CO line frequency using derived initial fit values"""
    # default initial fitting parameters, value not crtitical
    line_width = 2e-3
    baseline = 0
    initial_guess = [line_amplitude, line_position, line_width, baseline]
    try:
        popt, _ = curve_fit(
            fit_function_single_altitude_spectrum,
            frequency_grid / 1e9,
            spectrum,
            p0=initial_guess,
            sigma=None,
        )
        fitted_line_position = popt[1]
        fit_is_ok = True
    except RuntimeError:
        fitted_line_position = None
        fit_is_ok = False
    return [fit_is_ok, fitted_line_position]
