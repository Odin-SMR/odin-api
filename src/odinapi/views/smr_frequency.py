'''functionality to generate frequency per spectrum in scan'''


import numpy as np


class Smrl1bFreqspec(object):
    '''a class derived to calculate frequency
       vector from odin-smr L1B data
    '''
    def __init__(self):
        self.channels = []
        self.intmode = []
        self.freqcal = []
        self.skyfreq = []
        self.backend = []
        self.freqres = []
        self.restfreq = []

    def get_frequency(self, scan_h, ispec, numspec=2):
        ''' text
        '''
        self.channels = scan_h['channels'][numspec]
        self.intmode = scan_h['intmode'][numspec]
        self.freqcal = scan_h['ssb_fq'][numspec]
        self.skyfreq = scan_h['skyfreq'][ispec]
        self.backend = scan_h['backend'][numspec]
        self.freqres = scan_h['freqres'][numspec]
        self.restfreq = scan_h['restfreq'][ispec]
        # Note:
        # Backend == 1 -> AC1
        # Backend == 2 -> AC2
        # Backend == 3 -> AOS
        if self.backend == 3:
            freq = self.aos_freq()
        else:
            freq = self.ac_freq()
        # correcting Doppler in LO
        lofreq = scan_h['lofreq'][ispec] - (self.skyfreq - self.restfreq)
        if (self.skyfreq - lofreq) > 0.0:
            freq = lofreq + freq
        else:
            freq = lofreq - freq
        return np.array(freq)

    def aos_freq(self):
        '''aos frequency'''
        nchan = self.channels
        xvec = np.arange(0, nchan) - np.floor(nchan / 2)
        freq0 = self.freqcal[-1:-1:1]
        freq = (
            3900.0e6 * np.ones(1, nchan) - (np.polyval(freq0, xvec) - 2100.0e6)
        )
        return freq

    def ac_freq(self):
        '''ac frequency'''
        #
        # The IntMode reported by the correlator is interpreted as
        # a bit pattern. Because this bit pattern only describes ADC
        # 2-8, the real bit pattern is obtained by left shifting it
        # by one bit and adding one (i.e. it is assumed that ADC 1
        # is always on).
        # The sidebands used are represented by vector ssb, this is
        # hard-wired into the correlators:
        # ssb = [1, -1, 1, -1, -1, 1, -1, 1];
        # Analyse the correlator mode by reading the bit pattern
        # from right to left(!) and calculating a sequence of 16
        # integers whose meaning is as follows:
        #
        # n1 ssb1 n2 ssb2 n3 ssb3 ... n8 ssb8
        #
        # n1 ... n8 are the numbers of chips that are cascaded
        # to form a band.
        # ssb1 ... ssb8 are +1 or -1 for USB or SSB, respectively.
        # Unused ADCs are represented by zeros.
        #
        # examples (the "classical" modes):
        #
        # mode 0x00: ==> bit pattern 00000001
        # 8  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0
        # i.e. ADC 1 uses 8 chips in upper-side band mode
        #
        # mode 0x08: ==> bit pattern 00010001
        # 4  1  0  0  0  0  0  0  4 -1  0  0  0  0  0  0
        # i.e. ADC 1 uses 4 chips in upper-side band mode
        # and  ADC 5 uses 4 chips in lower-side band mode
        #
        # mode 0x2A: ==> bit pattern 01010101
        # 2  1  0  0  2  1  0  0  2 -1  0  0  2 -1  0  0
        # i.e. ADC 1 uses 2 chips in upper-side band mode
        # and  ADC 3 uses 2 chips in upper-side band mode
        # and  ADC 5 uses 2 chips in lower-side band mode
        # and  ADC 7 uses 2 chips in lower-side band mode
        #
        # mode 0x7F: ==> bit pattern 11111111
        # 1  1  1 -1  1  1  1 -1  1 -1  1  1  1 -1  1  1
        # i.e. ADC 1 uses 1 chip in upper-side band mode
        # and  ADC 2 uses 1 chip in lower-side band mode
        # and  ADC 3 uses 1 chip in upper-side band mode
        # and  ADC 4 uses 1 chip in lower-side band mode
        # and  ADC 5 uses 1 chip in lower-side band mode
        # and  ADC 6 uses 1 chip in upper-side band mode
        # and  ADC 7 uses 1 chip in lower-side band mode
        # and  ADC 8 uses 1 chip in upper-side band mode
        #
        if self.intmode & 256:
            freq = self.ac_intmode_and_256()
        else:
            if self.intmode & (1 << 4):
                freq = self.ac_intmode_and_16()
            else:
                freq = self.ac_intmode_other()
        if freq == []:
            print 'no frequencies, spectrum not frequency sorted!'
            return []
        return freq

    def get_seq_pattern(self):
        '''get the adc pattern'''
        ssbvec = [1, -1, 1, -1, -1, 1, -1, 1]
        mode = self.intmode & 255
        seqvec = np.zeros(16, dtype='int')
        mind = 0
        for bit_i in range(8):
            if (mode & (1 << bit_i)) != 0:
                mind = bit_i
            seqvec[2 * mind] = seqvec[2 * mind] + 1
        for bit_i in range(8):
            if seqvec[2 * bit_i] > 0:
                seqvec[2 * bit_i + 1] = ssbvec[bit_i]
            else:
                seqvec[2 * bit_i + 1] = 0
        return seqvec

    def ac_intmode_and_256(self):
        ''' get ac frequencies
        '''
        seqvec = self.get_seq_pattern()
        freq = np.zeros(shape=(8, 112))
        bands = [1, 2, 3, 4, 5, 6, 7, 8]  # default: use all bands
        if self.intmode & 512:
            # test for split mode
            if self.intmode & 1024:
                bands = [3, 4, 7, 8]  # upper band
            else:
                bands = [1, 2, 5, 6]  # lower band
        for adci in np.array(bands) - 1:
            if seqvec[2 * adci] > 0:
                dfreq = 1.0e6 / seqvec[2 * adci]
                if seqvec[2 * adci + 1] < 0:
                    dfreq = -dfreq
                for jind in range(1, seqvec[2 * adci] + 1):
                    mind = adci + jind - 1
                    # The frequencies are calculated by noting that
                    # two consecutive ADCs share the same internal
                    # SSB-LO:
                    freq[mind, :] = (self.freqcal[np.round(adci / 2)] *
                                     np.ones(112) + np.arange(0, 112, 1) *
                                     dfreq + (jind - 1) * 112 * dfreq)
        if self.intmode & 512:
            # for split mode keep used bands only
            freq = freq[bands, :]
        return freq

    def ac_intmode_and_16(self):
        '''get ac frequencies
        '''
        freq = []
        mode = self.intmode & 15
        if self.intmode & (1 << 5):
            if mode == 2:
                nchan = self.channels
                dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
                freq = self.freqcal[1] * np.ones(nchan) - dec_vec
            elif mode == 3:
                nchan = self.channels / 2
                inc_vec = np.arange(0, nchan, 1) * self.freqres
                dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
                freq = [
                    self.freqcal[3] * np.ones(nchan) - dec_vec,
                    self.freqcal[2] * np.ones(nchan) + inc_vec
                ]
            else:
                nchan = self.channels / 4
                inc_vec = np.arange(0, nchan, 1) * self.freqres
                dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
                freq = [
                    self.freqcal[2] * np.ones(nchan) - dec_vec,
                    self.freqcal[2] * np.ones(nchan) + inc_vec,
                    self.freqcal[3] * np.ones(nchan) - dec_vec,
                    self.freqcal[3] * np.ones(nchan) + inc_vec
                ]
        else:
            if mode == 2:
                nchan = self.channels
                inc_vec = np.arange(0, nchan, 1) * self.freqres
                freq = self.freqcal[0] * np.ones(nchan) + inc_vec
            elif mode == 3:
                nchan = self.channels / 2
                inc_vec = np.arange(0, nchan, 1) * self.freqres
                dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
                freq = [
                    self.freqcal[1] * np.ones(nchan) - dec_vec,
                    self.freqcal[0] * np.ones(nchan) + inc_vec
                ]
            else:
                nchan = self.channels / 4
                inc_vec = np.arange(0, nchan, 1) * self.freqres
                dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
                freq = [
                    self.freqcal[0] * np.ones(nchan) - dec_vec,
                    self.freqcal[0] * np.ones(nchan) + inc_vec,
                    self.freqcal[1] * np.ones(nchan) - dec_vec,
                    self.freqcal[1] * np.ones(nchan) + inc_vec
                ]
        return freq

    def ac_intmode_other(self):
        '''get ac frequencies
        '''
        mode = self.intmode & 15
        if mode == 1:
            nchan = self.channels
            inc_vec = np.arange(0, nchan, 1) * self.freqres
            freq = self.freqcal[0] * np.ones(nchan) + inc_vec
        elif mode == 2:
            nchan = self.channels / 2
            inc_vec = np.arange(0, nchan, 1) * self.freqres
            dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
            freq = [
                self.freqcal[0] * np.ones(nchan) + inc_vec,
                self.freqcal[1] * np.ones(nchan) - dec_vec
            ]
        elif mode == 3:
            nchan = self.channels / 4
            inc_vec = np.arange(0, nchan, 1) * self.freqres
            dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
            freq = [
                self.freqcal[1] * np.ones(nchan) - dec_vec,
                self.freqcal[0] * np.ones(nchan) + inc_vec,
                self.freqcal[3] * np.ones(nchan) - dec_vec,
                self.freqcal[2] * np.ones(nchan) + inc_vec
            ]
        else:
            nchan = self.channels / 8
            inc_vec = np.arange(0, nchan, 1) * self.freqres
            dec_vec = np.arange(nchan - 1, -1, -1) * self.freqres
            freq = [
                self.freqcal[0] * np.ones(nchan) - dec_vec,
                self.freqcal[0] * np.ones(nchan) + inc_vec,
                self.freqcal[1] * np.ones(nchan) - dec_vec,
                self.freqcal[1] * np.ones(nchan) + inc_vec,
                self.freqcal[2] * np.ones(nchan) - dec_vec,
                self.freqcal[2] * np.ones(nchan) + inc_vec,
                self.freqcal[3] * np.ones(nchan) - dec_vec,
                self.freqcal[3] * np.ones(nchan) + inc_vec
            ]
        return freq


class Smrl1bFreqsort(object):
    '''class derived to sort smr frequency spectra'''
    def __init__(self, sortmeth='from_middle', rm_edge_chs=True):
        self.freq = []
        self.ydata = []
        self.ssb = []
        self.ssb_ind = []
        self.channels_id = []
        self.sortmeth = sortmeth
        self.rm_edge_chs = rm_edge_chs

    def get_sorted_ac_spectrum(self, freq, ydata, bad_modules=None):
        '''get sorted ac specturm'''
        self.freq = np.array(freq)
        self.ydata = np.array(ydata)
        freq0 = np.array(self.freq)
        self.ac_filter(bad_modules)
        self.ac_freqsort(freq0)
        return self.freq, self.ydata, self.ssb, self.channels_id

    def ac_filter(self, bad_modules):
        '''filter spectrum, remove data from bad modules and edge channels'''
        self.ssb_ind = np.ones(896)
        self.channels_id = np.arange(896)
        for band in range(8):
            self.ssb_ind[band * 112:(band + 1) * 112] = band + 1
        if not bad_modules == [] or self.rm_edge_chs:
            indf = np.ones(896)
            if bad_modules is not None:
                # mark bad modules
                freqs = np.array(self.freq)
                freqs.shape = (8, 112)
                freqs = np.array([np.min(freqs, 1), np.max(freqs, 1)])
                for bad_i, _ in enumerate(bad_modules):
                    band_ind = np.nonzero(
                        (bad_modules[bad_i] >= freqs[0, :]) &
                        (bad_modules[bad_i] <= freqs[1, :])
                    )[0]
                    indf[(band_ind) * 112 + np.arange(0, 112, 1)] = 0
            if self.rm_edge_chs:
                # mark edge channels
                indf[np.append(np.arange(0, 896, 112),
                               np.arange(111, 896, 112))] = 0
            index = np.nonzero((indf > 0))[0]
            self.freq = self.freq[index]
            self.ydata = self.ydata[index]
            self.ssb_ind = self.ssb_ind[index]
            self.channels_id = self.channels_id[index]

    def ac_freqsort(self, freq0=None):
        '''sort frequency vector'''
        # Sort
        if self.sortmeth == 'from_middle':
            self.sort_from_middle(freq0)
        elif self.sortmeth == 'from_start':
            self.sort_from_start()
        elif self.sortmeth == 'from_end':
            self.sort_from_end()
        index = np.argsort(self.freq)
        self.freq = self.freq[index]
        self.ydata = self.ydata[index]
        self.ssb_ind = self.ssb_ind[index]
        self.channels_id = self.channels_id[index]
        for band in range(8):
            index = np.nonzero((self.ssb_ind == band + 1))[0]
            if index.shape[0] > 0:
                self.ssb.extend([band + 1, np.min(index) + 1,
                                 np.max(index) + 1])
            else:
                self.ssb.extend([band + 1, -1, -1])

    def sort_from_middle(self, freq0):
        '''Sort spectra from middle channel
           remove overlapping channels
           choose the channel which is closest to its
           sub-band frequency center
        '''
        freqs = np.array(freq0)
        freqs.shape = (8, 112)
        freqs = np.mean(freqs, 1)
        index = []
        for indi in range(self.freq.shape[0]):
            multi_f = np.nonzero((self.freq[indi] == self.freq))[0]
            if multi_f.shape[0] == 1:
                index.append(indi)
            else:
                # overlapping channels
                ssb_ind_i = np.array(self.ssb_ind[multi_f] - 1).astype(int)
                ssb_f0 = freqs[ssb_ind_i]
                inds = np.argsort(np.abs(ssb_f0 - self.freq[indi]))
                index.append(multi_f[inds[0]])
        index = np.unique(np.array(index))
        self.freq = self.freq[index]
        self.ydata = self.ydata[index]
        self.ssb_ind = self.ssb_ind[index]
        self.channels_id = self.channels_id[index]

    def sort_from_start(self):
        '''sort spectra from start channel'''
        nlen = self.freq.shape[0]
        [_, index] = np.unique(
            self.freq[np.arange(nlen - 1, -1, -1)], return_index=True
        )
        index = nlen - 1 - index
        self.freq = self.freq[index]
        self.ydata = self.ydata[index]
        self.ssb_ind = self.ssb_ind[index]
        self.channels_id = self.channels_id[index]

    def sort_from_end(self):
        '''sort spectra from end channel'''
        [_, index] = np.unique(self.freq, return_index=True)
        self.freq = self.freq[index]
        self.ydata = self.ydata[index]
        self.ssb_ind = self.ssb_ind[index]
        self.channels_id = self.channels_id[index]


def get_bad_ssb_modules(backend, spectra, freqvec, debug=False):
    '''get bad ssb modules'''
    if debug:
        bad_modules = np.array([], dtype=np.int)
    else:
        if backend == 1:
            bad_modules = np.array([1, 2])
        elif backend == 2:
            bad_modules = np.array([3])

    for numspec in range(spectra.shape[0]):
        tempspec = np.array(spectra[numspec])
        tempspec.shape = (8, 112)
        ytest = np.mean(tempspec, 1)
        badssb_ind = np.nonzero((ytest == 0))[0]
        if badssb_ind.shape[0] > 0:
            bad_modules = np.append(bad_modules, badssb_ind + 1)
    bad_modules = np.unique(bad_modules)
    # transform ssb number to mean frequency
    freq_modules = np.mean(freqvec, 1)
    bad_modules = freq_modules[bad_modules - 1]
    return bad_modules


def doppler_corr(skyfreq, restfreq, lofreq, freqvec):
    '''correcting for Doppler in LO'''
    lofreq = lofreq - (skyfreq - restfreq)
    if (skyfreq - lofreq) > 0.0:
        freqvec = (freqvec - lofreq)
    else:
        freqvec = -(lofreq - freqvec)
    return lofreq, freqvec


def freqfunc(lofreq, skyfreq, ssb_freq):
    '''simple freqvec'''
    nlen = 896
    freq = np.zeros(shape=(nlen,))
    seqvec = [1, 1, 1, -1, 1, 1, 1, -1,
              1, -1, 1, 1, 1, -1, 1, 1]
    mcount = 0
    for adci in range(8):
        if seqvec[2 * adci]:
            klen = seqvec[2 * adci] * 112
            dfreq = 1.0e6 / seqvec[2 * adci]
            if seqvec[2 * adci + 1] < 0:
                dfreq = -dfreq
            for jind in range(klen):
                freq[mcount + jind] = (
                    ssb_freq[adci / 2] + jind * dfreq
                )
            mcount += klen
    freqvec = np.zeros(shape=(nlen,))
    if skyfreq >= lofreq:
        for icount in range(nlen):
            freqi = freq[icount]
            freqi = lofreq + freqi
            freqi /= 1.0e9
            freqvec[icount] = freqi
    else:
        for icount in range(nlen):
            freqi = freq[icount]
            freqi = lofreq - freqi
            freqi /= 1.0e9
            freqvec[icount] = freqi
    return freqvec
