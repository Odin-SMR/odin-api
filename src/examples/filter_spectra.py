"""Functions for filtering lists of L1b spectra from Odin API v5"""
import numpy as np


def filter_by_param(spectra, low, high, param):
    """Filter scan by parameter value range

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        low (number): lower limit of range (inclusive)
        high (number): upper limit of range (inclusive)
        param (str): parameter to filter on

    Returns:
        filtered spectra list or dict
    """

    # Sanity check:
    if high < low:
        raise ValueError("High limit must not be lower than lower limit.")

    if "Data" in spectra and spectra["Type"] == "L1b":
        spectra["Data"] = filter_by_param(spectra["Data"], low, high, param)
    else:
        # Find matching indices:
        data = np.array(spectra[param])
        inds = np.where(np.logical_and(low <= data, data <= high))

        # Remove unmatched indices:
        for key, val in spectra.iteritems():
            if isinstance(val, list) or isinstance(val, np.ndarray):
                spectra[key] = np.array(spectra[key])[inds]

    return spectra


def filter_by_sbpath(spectra, low, high):
    """Filter scan by SBpath value range

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        low (number): lower limit of range (inclusive)
        high (number): upper limit of range (inclusive)

    Returns:
        filtered spectra list or dict
    """
    return filter_by_param(spectra, low, high, "SBpath")


def filter_by_tcal(spectra, low, high):
    """Filter scan by Tcal value range

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        low (number): lower limit of range (inclusive)
        high (number): upper limit of range (inclusive)

    Returns:
        filtered spectra list or dict
    """
    return filter_by_param(spectra, low, high, "Tcal")


def filter_by_altitude(spectra, low, high):
    """Filter scan by Altitude value range

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        low (number): lower limit of range (inclusive)
        high (number): upper limit of range (inclusive)

    Returns:
        filtered spectra list or dict
    """
    return filter_by_param(spectra, low, high, "Altitude")


def filter_by_latitude(spectra, low, high):
    """Filter scan by Latitude value range

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        low (number): lower limit of range (inclusive)
        high (number): upper limit of range (inclusive)

    Returns:
        filtered spectra list or dict
    """
    return filter_by_param(spectra, low, high, "Latitude")


def filter_by_quality(spectra, reject=0xFFFFFFFF, require=0x0):
    """Filter scan by Quality values

    Args:
        spectra (list or dict): list of L1b spectra or L1b dict
        reject (number): bit mask of quality flags to reject (default: all)
        require (number): bit mask of quality flags to require (default: none)

    Returns:
        filtered spectra list or dict
    """

    # Sanity check:
    if (reject & require) != 0:
        raise ValueError(
            "Require and reject masks must be mutually exclusive.")

    if "Data" in spectra and spectra["Type"] == "L1b":
        spectra["Data"] = filter_by_quality(spectra["Data"], reject, require)
    else:
        # Find matching indices:
        data = np.array(spectra["Quality"])
        inds = np.where(np.logical_and(
            (data & require) == require, (data & reject) == 0x0))

        # Remove unmatched indices:
        for key, val in spectra.iteritems():
            if isinstance(val, list) or isinstance(val, np.ndarray):
                spectra[key] = np.array(spectra[key])[inds]

    return spectra
