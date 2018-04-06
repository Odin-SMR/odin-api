'''frequency correction tools for odin-api
'''


import numpy as N
from scipy.optimize import curve_fit


class Freqcorr572(object):
    '''A class derived for performing frequency
    calibration of data from Odin/SMR 572 frontend
    '''
    def __init__(self, freqgrid, spectra, altitude):
        self.freqgrid = freqgrid
        self.spectra = spectra
        self.altitude = N.array(altitude, dtype=float)
        self.correction_is_ok = False
        self.fdiff = 0
        self.median_tb = []
        self.popt = []

    def altitude_check(self):
        '''check that scan covering
        40 to 60 km in altitude
        '''
        return N.min(self.altitude) < 40e3 and N.max(self.altitude) > 60e3

    def get_initial_fit_values(self, tbmin=10):
        '''identify frequency and Tb of the line with
        lowest frequency in median spectra of scan,
        these values will be used as starting values
        for a more detailed fit
        '''
        high_altitude_index = N.nonzero(self.altitude > 20e3)[0]
        if self.altitude_check():
            # median is preferable to use
            self.median_tb = N.median(self.spectra[high_altitude_index], 0)
        else:
            # if we do not have much measurements from
            # low altitude we must use mean instead of median,
            # because taking the median can resulting in
            # that all lines are removed from spectra
            self.median_tb = N.mean(self.spectra[high_altitude_index], 0)
        high_tb_index = N.nonzero(self.median_tb > tbmin)[0]
        if high_tb_index.shape[0] < 2:
            frequency_initial_guess = None
            tb_initial_guess = None
            initial_guess_is_ok = False
        else:
            tb_initial_guess = N.max(
                self.median_tb[
                    N.nonzero(
                        self.freqgrid <=
                        self.freqgrid[high_tb_index][0] + 100e6
                    )[0]
                ]
            )
            frequency_initial_guess = self.freqgrid[
                N.nonzero(self.median_tb == tb_initial_guess)[0]
            ][0] / 1e9
            initial_guess_is_ok = True
        return (
            initial_guess_is_ok,
            frequency_initial_guess,
            tb_initial_guess
        )

    def fit_data(self, tb_initial, f_initial):
        '''try to fit data using derived initial fit values'''
        # default initial fitting parameters, value not crtitical
        linewidth_1 = 2e-3
        line_amp2 = 100
        linewidth_2 = 2e-2
        co_o3_fdiff = 0.247
        para0 = [
            tb_initial, f_initial, linewidth_1, line_amp2,
            linewidth_2
        ]
        try:
            popt, _ = curve_fit(
                fit_func,
                self.freqgrid / 1e9,
                self.median_tb,
                p0=para0,
                sigma=10)
            self.popt = popt
            freq1 = popt[1]
            freq2 = popt[1] + co_o3_fdiff
            fit_is_ok = True
        except RuntimeError:
            freq1 = None
            freq2 = None
            fit_is_ok = False
        return (fit_is_ok, freq1, freq2)

    def get_tb_profile(self, freq1, freq2):
        '''extract tb as function of altitude for the estimated
        line center frequencies. This data will be used to
        identify species
        '''
        tb_profile = []
        for spectrum in self.spectra:
            if (freq1 > self.freqgrid[0] / 1e9 and
                    freq2 < self.freqgrid[-1] / 1e9):
                tbi = N.interp([freq1, freq2], self.freqgrid / 1e9,
                               spectrum)
                tb_profile.append([tbi[0], tbi[1]])
            elif freq1 > self.freqgrid[0] / 1e9:
                tbi = N.interp([freq1], self.freqgrid / 1e9,
                               spectrum)
                tb_profile.append([tbi[0], N.nan])
            elif freq2 < self.freqgrid[-1] / 1e9:
                tbi = N.interp([freq1], self.freqgrid / 1e9,
                               spectrum)
                tb_profile.append([N.nan, tbi[0]])
            else:
                tb_profile.append([N.nan, N.nan])
        return N.array(tb_profile)

    def identify_species_by_profile(self,
                                    tb_profile,
                                    zmin=40,
                                    zmax=60,
                                    cutoff=-0.0045):
        '''identify species from the change (between 40 and 60 km)
        in tb profile and derive the frequency correction to apply
        '''
        if self.altitude[0] > self.altitude[-1]:
            tb_diff = N.interp([zmin, zmax], self.altitude[-1::-1] / 1e3,
                               tb_profile[-1::-1, 0])
        else:
            tb_diff = N.interp([zmin, zmax], self.altitude / 1e3,
                               tb_profile[:, 0])
        tbchange = (tb_diff[1] - tb_diff[0]) / 20e3
        return tbchange > cutoff

    def identify_species_by_lines(self):
        '''identify species by checking if two lines were found'''
        return self.popt[0] > 10 and self.popt[3] > 10

    def run_freq_corr(self, co_true=576.268):
        '''run the frequency correction'''
        [initial_guess_is_ok, f_initial, tb_initial] = \
            self.get_initial_fit_values()
        if initial_guess_is_ok:
            [fit_is_ok, freq1, freq2] = self.fit_data(
                tb_initial, f_initial)
            if fit_is_ok:
                altitud_is_ok = self.altitude_check()
                if altitud_is_ok:
                    # identify species from tb(ztan) gradient
                    tb_profile = self.get_tb_profile(freq1, freq2)
                    co_found = self.identify_species_by_profile(
                        tb_profile)
                else:
                    # possibly identify species if two lines are
                    # observed
                    co_found = self.identify_species_by_lines()
                if co_found:
                    self.fdiff = freq1 - co_true
                    self.correction_is_ok = True


def fit_func(freqgrid,
             line_amp1,
             line_pos1,
             line_width1,
             line_amp2,
             line_width2):
    '''fitting function for scan median spectra'''
    co_o3_fdiff = 0.247
    part1 = line_amp1 * N.exp(
        -((freqgrid - line_pos1) / line_width1)**2
    )
    part2 = line_amp2 * N.exp(
        -((freqgrid - (line_pos1 + co_o3_fdiff)) / line_width2)**2
    )
    return part1 + part2
