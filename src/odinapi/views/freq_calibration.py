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
        self.correction_is_ok = 0
        self.fdiff = 0
        self.median_tb = []
        self.popt = []

    def altitude_check(self):
        '''check that scan covering
        40 to 60 km in altitude
        '''
        if N.min(self.altitude) < 40e3 and N.max(self.altitude) > 60e3:
            return 1
        else:
            return 0

    def get_initial_fit_values(self, tbmin=10):
        '''identify frequency and Tb of the line with
        lowest frequency in median spectra of scan,
        these values will be used as starting values
        for a more detailed fit
        '''
        okind = N.nonzero((self.altitude > 20e3))[0]
        if self.altitude_check():
            # median is preferable to use
            self.median_tb = N.median(self.spectra[okind], 0)
        else:
            # if we do not have much measurements from
            # low altitude we must use mean instead of median,
            # because taking the median can resulting in
            # that all lines are removed from spectra
            self.median_tb = N.mean(self.spectra[okind], 0)
        ind_t1 = N.nonzero((self.median_tb > tbmin))[0]
        if ind_t1.shape[0] < 2:
            f_initial = 0
            tb_initial = 0
            initial_guess_is_ok = 0
        else:
            ind_t2 = N.nonzero((self.median_tb > 10) & (
                self.median_tb < self.median_tb[ind_t1[0]] + 0.1))[0]
            ind_t3 = N.argsort(self.median_tb[ind_t2])[-1]
            f_initial = self.freqgrid[ind_t2[ind_t3]] / 1e9
            tb_initial = self.median_tb[ind_t2[ind_t3]]
            initial_guess_is_ok = 1
        return [initial_guess_is_ok, f_initial, tb_initial]

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
            # diff = N.sqrt(
            #    N.mean(
            #        N.abs(
            #            fit_func(self.freqgrid / 1e9, popt[0], popt[1], popt[
            #                2], popt[3], popt[4]) - self.median_tb)**2))
            self.popt = popt
            freq1 = popt[1]
            freq2 = popt[1] + co_o3_fdiff
            fit_is_ok = 1
        except RuntimeError:
            freq1 = 0
            freq2 = 0
            fit_is_ok = 0
        return [fit_is_ok, freq1, freq2]

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
        co_found = 0
        if self.altitude[0] > self.altitude[-1]:
            tb_diff = N.interp([zmin, zmax], self.altitude[-1::-1] / 1e3,
                               tb_profile[-1::-1, 0])
        else:
            tb_diff = N.interp([zmin, zmax], self.altitude / 1e3,
                               tb_profile[:, 0])
        tbchange = (tb_diff[1] - tb_diff[0]) / 20e3
        if tbchange > cutoff:
            co_found = 1
        return co_found

    def identify_species_by_lines(self):
        '''identify species by checking if two lines were found'''
        co_found = 0
        if self.popt[0] > 10 and self.popt[3] > 10:
            # two lines were identified
            co_found = 1
        return co_found

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
                    self.correction_is_ok = 1


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
