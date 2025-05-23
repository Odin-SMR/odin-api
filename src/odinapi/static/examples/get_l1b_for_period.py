"""Functions for getting L1b scans and spectra from Odin API v5"""

from datetime import timedelta

from dateutil import parser as dateparser
import requests
import numpy as np


API_ROOT = "http://odin.rss.chalmers.se/rest_api/v5"


def get_scans_for_date(freqmode, date, api_root=API_ROOT, retries=0):
    """Get scans from freqmode for date

    Args:
        freqmode (int): frequency mode to look at
        date (str or datetime): date to look at
        api_root (str): root URI for the API

    Returns:
        List of scan log data for frequency mode and date
    """

    # Sanity check arguments:
    if isinstance(date, str):
        date = dateparser.parse(date).date()

    for attempt in range(retries + 1):
        try:
            req = requests.get(
                "{}/freqmode_info/{}/{}/".format(
                    api_root, date.isoformat(), int(freqmode)
                ),
                timeout=(60, 60),
            )
            break
        except requests.exceptions.ReadTimeout:
            pass
    if req.status_code == 200:
        return req.json()["Data"]
    else:
        return []


def get_scans_for_period(
    freqmode, first, last, api_root=API_ROOT, retries=0, verbose=False
):
    """Get scans from freqmode from first to last date inclusive

    Args:
        freqmode (int): frequency mode to look at
        first (str or datetime): first date in range
        last (None, str or datetime): last date in range or None
        api_root (str): root URI for the API
        verbose (bool): toggle print-outs

    Returns:
        List of scan log data for frequency mode and date range
    """

    # Sanity check arguments:
    if isinstance(first, str):
        first = dateparser.parse(first).date()
    if isinstance(last, str):
        last = dateparser.parse(last).date()
    if last is None:
        last = first

    if last < first:
        raise ValueError("Last date must not be before first date.")

    # Loop over days:
    delta = timedelta(days=1)
    day = first
    scans = []
    while day <= last:
        # lookup day
        if verbose:
            print("Looking up {}...".format(day))
        for attempt in range(retries + 1):
            try:
                req = requests.get(
                    "{}/freqmode_info/{}/".format(api_root, day.isoformat()),
                    timeout=(60, 60),
                )
                break
            except requests.exceptions.ReadTimeout:
                pass
        if req.status_code == 200:
            for datum in req.json()["Data"]:
                # if fm exists for day lookup fm and add scans to list
                if datum["FreqMode"] == int(freqmode):
                    scans.extend(get_scans_for_date(freqmode, day, api_root, retries))
                    break
        day += delta

    return scans


def interpolate_spectrum(spectrum, freqs, new_freqs):
    """Interpolate spectrum to the given frequency grid"""
    return np.interp(new_freqs, freqs, spectrum)


def interpolate_spectra(spectra, freqs, new_freqs):
    """Interpolate list of spectra to the given frequency grid"""
    return [
        interpolate_spectrum(spectra[n], freqs[n], new_freqs)
        for n in range(len(spectra))
    ]


def extend_dict(dikt, data):
    """Extend dikt with data of same format as dikt

    Args:
        dikt (dict): dictionary to extend
        data (dict): dictionary to extend by (same format as dict)

    Returns:
        Nothing, works directly on dikt
    """
    for key, val in data.items():
        try:
            if isinstance(val, list):
                if key == "Spectrum" and "Frequency" in dikt:
                    val = interpolate_spectra(
                        val,
                        [
                            np.array(data["Frequency"]["IFreqGrid"]) + lof
                            for lof in data["Frequency"]["LOFreq"]
                        ],
                        (
                            np.array(dikt["Frequency"]["IFreqGrid"])
                            + dikt["Frequency"]["LOFreq"][0]
                        ),
                    )
                elif (
                    key in ["IFreqGrid", "ChannelsID"] and "IFreqGrid" in dikt
                ) or key == "TrecSpectrum":
                    continue
                dikt[key].extend(val)
            elif isinstance(val, dict):
                extend_dict(dikt[key], val)
        except KeyError:
            dikt[key] = val


def get_spectra_for_period(
    freqmode, first, last=None, api_root=API_ROOT, retries=0, verbose=False
):
    """Get scans from freqmode from first to last date inclusive

    Args:
        freqmode (int): frequency mode to look at
        first (str or datetime): first date in range
        last (None, str or datetime): last date in range or None
        api_root (str): root URI for the API
        verbose (bool): toggle print-outs

    Returns:
        List of spectra for frequency mode and date range
    """

    # get spectra:
    spectra = {}
    scans = get_scans_for_period(freqmode, first, last, api_root, retries, verbose)
    for n, scan in enumerate(scans):
        for attempt in range(retries + 1):
            try:
                req = requests.get(scan["URLS"]["URL-spectra"], timeout=(60, 60))
                break
            except requests.exceptions.ReadTimeout:
                pass

        if req.status_code == 200:
            data = req.json()["Data"]
            extend_dict(spectra, data)
            print(
                "Got scan {} of {} ({:.0f}%)".format(
                    n + 1,
                    len(scans),
                    (100 * (n + 1)) / len(scans),
                )
            )
        else:
            print(
                "Failed to get scan {} of {} ({:.0f}%)".format(
                    n + 1,
                    len(scans),
                    (100 * (n + 1)) / len(scans),
                )
            )

    return spectra
