import numpy as N
from scipy.optimize import curve_fit


class FreqCorr_572():
    '''A class derived for performing frequency 
       calibration of data from Odin/SMR 572 frontend'''
    def __init__(self, freqgrid, spectra, altitude):
        self.freqgrid = freqgrid
        self.spectra = spectra
        self.altitude = altitude
        self.CO = 0
        self.altitude_is_ok = 0
        self.correction_is_ok = 0
        self.initial_guess_is_ok = 0
        self.fit_is_ok = 0
    def altitude_check(self):
        '''check that scan covering
           40 to 60 km in altitude'''
        if N.min(self.altitude) < 40e3 and N.max(self.altitude)>60e3:
           self.altitude_is_ok = 1

    def get_initial_fit_values(self, tbmin=10):
        '''identify frequency and Tb of the line with 
           lowest frequency in median spectra of scan,
           these values will be used as starting values
           for a more detailed fit'''

        okind = N.nonzero( (self.altitude>20e3) )[0]
        self.y = N.median( self.spectra[okind], 0 )
        self.x = self.freqgrid/1e9
        ind_t1 = N.nonzero((self.y>tbmin))[0]
        if ind_t1.shape[0]<2:
            self.initial_guess_is_ok = 0
        else:
            ind_t2 = N.nonzero( (self.y>10) & ( self.x < self.x[ind_t1[0]]+0.1 ) )[0]
            ind_t3 = N.argsort(self.y[ind_t2])[-1]
            self.fi = self.x[ind_t2[ind_t3]]
            self.tbi = self.y[ind_t2[ind_t3]]
            self.initial_guess_is_ok = 1

    def fit_data(self, c1=2e-3, a2=100 ,c2=2e-2, co_o3_fdiff=0.247):
        '''try to fit data using derived initial fit values'''

        p0 = [self.tbi, self.fi, c1, a2, c2]
        try:
            popt, pcov = curve_fit(self.fit_func, self.x, self.y, p0=p0, sigma=10)
            self.diff = N.sqrt(N.mean(N.abs(self.fit_func(self.x,popt[0],popt[1],popt[2],popt[3],popt[4])-self.y)**2))
            self.popt = popt
            self.f1 = popt[1]
            self.f2 = popt[1] + co_o3_fdiff
            self.fit_is_ok = 1
        except:
            self.fit_is_ok = 0

    def get_tb_profile(self):
        '''extract tb as function of altitude for the estimated line
           center frequencies. This data will be used to identify species'''
        tb = []
        for y in self.spectra:
            if self.f1 > self.x[0] and self.f2 < self.x[-1]:
                tbi = N.interp( [self.f1, self.f2], self.x, y)
                tb.append( [tbi[0], tbi[1]] )
            elif self.f1 > self.x[0]:
                tbi = N.interp( [self.f1], self.x, y)
                tb.append( [tbi[0], N.nan] )
            elif self.f2 < self.x[-1]:
                tbi = N.interp( [self.f1], self.x, y)
                tb.append( [N.nan,tbi[0]] )
            else:
                tb.append( [N.nan, N.nan] )
        self.tb = N.array(tb)

    def identify_species(self, zmin=40, zmax=60, cutoff=-0.0045, co_true=576.268):
        '''identify species from the change (between 40 and 60 km) in tb profile
           and derive the frequency correction to apply'''
        if self.altitude[0] > self.altitude[-1]:
            self.tb_diff = N.interp( [zmin, zmax], self.altitude[-1::-1]/1e3, self.tb[-1::-1,0])

        else:
            self.tb_diff = N.interp( [zmin, zmax], self.altitude/1e3, self.tb[:,0])
        Tbchange = (self.tb_diff[1]-self.tb_diff[0])/20e3
        if Tbchange > cutoff:
            self.CO = 1
            self.fdiff = self.f1 - co_true
        else:
            self.CO = 0


    def fit_func(self, x, a1, b1, c1, a2, c2, co_o3_fdiff=0.247):
        '''fitting function for scan median spectra'''
        return a1 * N.exp(-( (x-b1)/c1 )**2) + a2 * N.exp(-( ( x- (b1 + co_o3_fdiff) )/c2 )**2)


    def run_freq_corr(self):
        '''run the frequency correction'''
        self.altitude_check()
        if self.altitude_is_ok:
            self.get_initial_fit_values()
            if self.initial_guess_is_ok:
                self.fit_data()
                if self.fit_is_ok:
                    self.get_tb_profile()
                    self.identify_species()
                    if self.CO:
                        self.correction_is_ok = 1


