"""Functions for getting optional arguments from endpoints"""
from datetime import datetime

from dateutil.parser import parse as parse_datetime
from flask import request


def str2bool(val):
    booleans = {
        "true": True,
        "yes": True,
        "y": True,
        "1": True,
        "false": False,
        "no": False,
        "n": False,
        "0": False,
    }
    try:
        val = booleans[val.lower()]
    except KeyError:
        raise ValueError
    return val


def get_string(arg):
    return request.args.get(arg)


def get_int(arg):
    val = request.args.get(arg)
    if not val:
        return
    try:
        return int(val)
    except ValueError:
        raise ValueError('Could not convert to integer: %r' % val)


def get_bool(arg):
    val = request.args.get(arg)
    if not val:
        return
    try:
        return str2bool(str(val))
    except ValueError:
        raise ValueError('Could not convert to boolean: %r' % val)


def get_float(arg=None, val=None):
    if not val:
        val = request.args.get(arg)
    if not val:
        return
    try:
        return float(val)
    except ValueError:
        raise ValueError('Could not convert to number: %r' % val)


def get_list(arg):
    return request.args.getlist(arg) or None


def get_datetime(arg=None, val=None):
    if not val:
        val = request.args.get(arg)
    if not val:
        return
    if isinstance(val, datetime):
        return val
    try:
        return parse_datetime(val)
    except ValueError:
        raise ValueError('Bad time format: %r' % val)
