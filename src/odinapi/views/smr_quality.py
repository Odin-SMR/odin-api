"""quality check of a scan"""
import numpy as np


EARTH1 = 0x0001
MOON1 = 0x0002
GALAX1 = 0x0004
SUN1 = 0x0008
MOONMB = 0x0200


class QualityControl:
    """class derived to check quality"""

    def __init__(self, specdata, refdata):
        self.refdata = refdata
        self.specdata = specdata
        self.quality = specdata["quality"]
        self.zerolagvar = []

    def run_control(self):
        """Quality check of a scan
        =====================================================
        1. check Tspill  - outside of valid range
        2. check Trec    - outside of valid range
        3. check Noise   - outside of valid range
        4. check Scan    - corrupt scanning (tangent altitude is not
                           decreasing or increasing as expected)
        5. check nr of atmospheric spectra
        Quality check of each spectrum of a scan
        =====================================================
        1. Tb            - outside of valid range (0-300)
        2. Sig           - corrupt integration time
        3. Ref           - observation sequence
        4. Ref           - integration times
        """
        self.check_tspill()
        self.check_trec()
        self.check_noise()
        self.check_scan()
        self.check_nr_of_spec()
        self.check_tb()
        self.check_int()
        self.check_obs_sequence()
        self.filter_references()
        self.check_ref_inttime()
        self.check_moon_in_mainbeam()
        self.get_zerolagvar()

    def check_tspill(self):
        """check tspill is ok"""
        qual = 0x0001
        tspill_min = 2
        tspill_max = 16
        if not (
            self.specdata["tspill"][0] >= tspill_min
            and self.specdata["tspill"][0] <= tspill_max
        ):
            self.quality = self.quality + qual

    def check_trec(self):
        """check trec is ok"""
        qual = 0x0002
        trec_min = 2000
        trec_max = 8000
        if not (
            self.specdata["tsys"][2] >= trec_min
            and self.specdata["tsys"][2] <= trec_max
        ):
            self.quality = self.quality + qual

    def check_noise(self):
        """check noise is ok"""
        qual = 0x0004
        noise_min = 0.5
        noise_max = 6
        bandwidth = 1e6
        if (
            self.specdata["efftime"][2] > self.specdata["inttime"][2] * 2
            or self.specdata["efftime"][2] < self.specdata["inttime"][2] * 0.5
        ):
            # estimated noise is suspicious
            # low or high, make a new estimate
            self.estimate_efftime(bandwidth)
        noise = (
            self.specdata["tsys"][2]
            / (self.specdata["efftime"][2::] * bandwidth) ** 0.5
        )

        test = np.nonzero((noise <= noise_min) | (noise >= noise_max))[0]
        if not test.shape[0] == 0:
            self.quality = self.quality + qual

    def estimate_efftime(self, bandwidth, zdiff=10e3):
        """estimate integration efftime"""
        tbspec = np.array(self.specdata["spectrum"])
        zmax = np.max(self.specdata["altitude"][2::])
        okzind = np.nonzero(self.specdata["altitude"][2::] >= zmax - zdiff)[0]
        efft = np.zeros((okzind.shape[0], 8))
        for band in range(8):
            ind1 = self.specdata["frequency"]["SubBandIndex"][0][band]
            ind2 = self.specdata["frequency"]["SubBandIndex"][1][band]
            if ind1 != -1:
                bandtb = tbspec[okzind + 2, ind1 - 1 : ind2]
                meantb = np.array([np.mean(bandtb, 1)])
                meantb = np.repeat(meantb, bandtb.shape[1], 0).transpose()
                msqe = np.mean((bandtb - meantb) ** 2, 1)
                efft[:, band] = (
                    self.specdata["tsys"][2] ** 2
                    / msqe
                    / bandwidth
                    / self.specdata["inttime"][okzind + 2]
                )
        efft = np.max(np.mean(efft, 0))
        self.specdata["efftime"] = self.specdata["inttime"] * efft

    def check_scan(self):
        """check that scanning is either upwards or downwards"""
        qual = 0x0008
        altdiff = np.diff(self.specdata["altitude"][2::])
        test = (
            np.nonzero((altdiff + 0.1 >= 0))[0].shape[0] == altdiff.shape[0]
            or np.nonzero((altdiff - 0.1 <= 0))[0].shape[0] == altdiff.shape[0]
        )
        if not test:
            self.quality = self.quality + qual

    def check_nr_of_spec(self):
        """check that scan contains at least n target spectra"""
        qual = 0x0010
        nmin = 5
        sig_ind = np.nonzero((self.specdata["type"] == 8))[0]
        if not sig_ind.shape[0] >= nmin:
            self.quality = self.quality + qual

    def check_tb(self):
        """check Tb, search for physically unrealistic values"""
        qual = 0x0020
        tb_min = -15
        tb_max = 280
        for ind, spec in enumerate(self.specdata["spectrum"]):
            if ind < 2:
                # do not consider calibration spectrum here
                continue
            speci = np.array(spec)
            qtest = np.nonzero((speci <= tb_min) | (speci >= tb_max))[0]
            if not qtest.shape[0] == 0:
                self.quality[ind] = self.quality[ind] + qual

    def check_int(self):
        """check that integration times are valid"""
        qual = 0x0040
        ok_inttimes = [0.854, 1.854, 3.854]
        timediff = 0.01
        # inttime must be within ok_inttimes+-dt to be ok
        ind = np.nonzero(
            (np.abs(self.specdata["inttime"] - ok_inttimes[0]) > timediff)
            & (np.abs(self.specdata["inttime"] - ok_inttimes[1]) > timediff)
            & (np.abs(self.specdata["inttime"] - ok_inttimes[2]) > timediff)
        )[0]
        self.quality[ind] = self.quality[ind] + qual

    def check_obs_sequence(self):
        """check if atmospheric spectrum is collected between
        two accepted sky beam 1 references
        """
        qual = 0x0080
        for ind, stw in enumerate(self.specdata["stw"]):
            if ind < 2:
                continue
            ind1 = np.atleast_1d(self.refdata["stw"] < stw).nonzero()[0]
            ind2 = np.atleast_1d(self.refdata["stw"] > stw).nonzero()[0]
            if ind1.shape[0] == 0 or ind2.shape[0] == 0:
                self.quality[ind] = self.quality[ind] + qual
                continue
            if ind1.shape[0] < 2:
                self.quality[ind] = self.quality[ind] + qual
                continue
            if (
                self.refdata["mech_type"][ind1[-2]] != "SK1"
                or self.refdata["mech_type"][ind1[-1]] != "SK1"
                or self.refdata["mech_type"][ind2[0]] != "SK1"
            ):
                self.quality[ind] = self.quality[ind] + qual
                continue
            test1 = np.atleast_1d(
                (self.refdata["skybeamhit"][ind1[-1]] & EARTH1 == EARTH1)
                | (self.refdata["skybeamhit"][ind1[-1]] & MOON1 == MOON1)
                | (self.refdata["skybeamhit"][ind1[-1]] & SUN1 == SUN1)
            ).nonzero()[0]
            test2 = np.atleast_1d(
                (self.refdata["skybeamhit"][ind2[0]] & EARTH1 == EARTH1)
                | (self.refdata["skybeamhit"][ind2[0]] & MOON1 == MOON1)
                | (self.refdata["skybeamhit"][ind2[0]] & SUN1 == SUN1)
            ).nonzero()[0]
            if test1.shape[0] != 0 or test2.shape[0] != 0:
                self.quality[ind] = self.quality[ind] + qual

    def check_ref_inttime(self):
        """check that surrounding references integration time are the same"""
        qual = 0x0100
        for ind, stw in enumerate(self.specdata["stw"]):
            if ind < 2:
                continue
            ind1 = np.nonzero((self.refdata["stw"] < stw))[0]
            ind2 = np.nonzero((self.refdata["stw"] > stw))[0]
            if ind1.shape[0] == 0 or ind2.shape[0] == 0:
                self.quality[ind] = self.quality[ind] + qual
                continue
            if (
                np.abs(
                    self.refdata["inttime"][ind1[-1]] - self.refdata["inttime"][ind2[0]]
                )
                > 0.2
            ):
                self.quality[ind] = self.quality[ind] + qual

    def check_moon_in_mainbeam(self):
        """check if moon is in the main beam"""
        qual = 0x0200
        ind1 = np.nonzero((self.specdata["skybeamhit"][2::] & MOONMB == MOONMB))[0]
        if ind1.shape[0] != 0:
            self.quality[ind1 + 2] = self.quality[ind1 + 2] + qual

    def filter_references(self):
        """identify reference signals that we do not trust,
        1. we only trust signals from SK1 (skybeam 1) if the
           previous signal also was SK1 and not if SK1
        2. we only use SK1 beam if it does not hit an object
        """
        # check which SK1 references the beam hit an object
        test1 = np.nonzero(
            (self.refdata["sig_type"] == "REF") & (self.refdata["mech_type"] == "SK1")
        )[0]
        test2 = np.nonzero(
            (self.refdata["skybeamhit"] & EARTH1 == EARTH1)
            | (self.refdata["skybeamhit"] & MOON1 == MOON1)
            | (self.refdata["skybeamhit"] & SUN1 == SUN1)
        )[0]
        badind1 = np.intersect1d(test1, test2)
        # check that previous ref is SK1
        badind2 = np.nonzero(
            (self.refdata["sig_type"] == "REF") & (self.refdata["mech_type"] != "SK1")
        )[0]
        # add all following references to index list of untrusted references
        badind2 = np.unique(np.union1d(badind2, badind2 + 1))
        # combine bad indexes
        badind = np.unique(np.union1d(badind1, badind2))
        # store the good referenes
        allind = np.arange(self.refdata["sig_type"].shape[0])
        okind = np.setdiff1d(allind, badind)
        for key in self.refdata:
            self.refdata[key] = self.refdata[key][okind]

    def get_zerolagvar(self):
        """identify the power variation of the two surrounding
        reference measurements
        """
        ones = np.array(np.ones(8) * -1).tolist()
        for ind, stw in enumerate(self.specdata["stw"]):
            if ind < 2:
                self.zerolagvar.append(ones)
                continue
            ind1 = np.nonzero((self.refdata["stw"] < stw))[0]
            ind2 = np.nonzero((self.refdata["stw"] > stw))[0]
            if ind1.shape[0] == 0 or ind2.shape[0] == 0:
                self.zerolagvar.append(ones)
                continue
            zero1 = np.array(self.refdata["cc"][ind1[-1]])
            zero2 = np.array(self.refdata["cc"][ind2[0]])
            gaindiff = np.abs(zero1 - zero2)
            gain = np.array((zero1 + zero2) / 2.0)
            frac = np.array(ones)
            index = np.nonzero((gain > 0))[0]
            frac[index] = gaindiff[index] / gain[index] * 100.0
            self.zerolagvar.append(np.around(frac, decimals=4).tolist())


class QualityDisplay:
    """class derived to extract information from
    odin level1b quality flag
    """

    def __init__(self, quality):
        self.quality = quality
        self.qualdict = {
            "Tspill": [0x1, "Tspill is outside of valid range. "],
            "Trec": [0x2, "Trec is outside of valid range. "],
            "Noise": [0x4, "Noise is outside of valid range. "],
            "Scanning": [
                0x8,
                "Tangent altitude is not decreasing or " + "increasing as expected. ",
            ],
            "nr of spectra": [
                0x10,
                "The scan consists of less than " + "five spectra. ",
            ],
            "Tb": [0x20, "Tb is outside of valid range. "],
            "Tint": [0x40, "Integration time is outside valid range. "],
            "Ref1": [
                0x80,
                "At least one atmospheric spectrum is not "
                + "collected between two sky beam 1 references. ",
            ],
            "Ref2": [
                0x100,
                "Surrounding references have different " + "integration times. ",
            ],
            "Moon": [0x200, "The moon is within the main beam. "],
        }

    def get_flaglist(self):
        """identify which bits are non zero"""
        flaglist = []
        for key in self.qualdict:
            if self.quality & self.qualdict[key][0] != 0:
                flaglist.append(key)
        return flaglist

    def get_flaginfo(self):
        """create a message that summarises
        the qualiy
        """
        flaglist = self.get_flaglist()
        message = ""
        if flaglist != []:
            for item in flaglist:
                if message == "":
                    message = (
                        "The Quality of Level1B data " + "for this scan is limited: "
                    )
                message = message + self.qualdict[item][1]
        for ind in range(0, len(message) // 180):
            message = (
                message[0 : 1 + 180 * (ind + 1) + 3 * ind]
                + "-\n"
                + message[1 + 180 * (ind + 1) + 3 * ind : :]
            )
        return message
