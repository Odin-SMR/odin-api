#!/usr/bin/env python

# First import requests to allow us to make calls to the API:
import requests

# Start by making a request to the root URI of the VDS API:
r0 = requests.get("http://odin.rss.chalmers.se/rest_api/v4/vds/")

# The request contains the returned JSON object, which in Python is a
# dictionary. This can be printed or inspected to find out its keys and
# contents. Let"s assume that we have done that, or that we have read the API
# documentation, so that we know that "FreqMode" is a key. Use this to single
# out the frequency mode of interest, in this case 2 (the result of the filter
# is a list, so [0] is used to get the object we want):
FM2 = [
    x for x in r0.json()["VDS"]
    if x["FreqMode"] == 2
][0]

# Make a new request using the URI provided in the JSON object, and single out
# the species O3 and the instrument MLS. For convenience, since there are
# multiple intruments with O3 and MLS has multiple species, we do filter bothe
# these properties in a single step:
r1 = requests.get(FM2["URL-collocation"])
O3MLS = [
    x for x in r1.json()["VDS"]
    if x["Species"] == "O3" and x["Instrument"] == "mls"
][0]

# Repeat for the new object and a date of interest:
r2 = requests.get(O3MLS["URL"])
day = [
    x for x in r2.json()["VDS"]
    if x["Date"] == "2012-09-15"
][0]

# To get the detailed information about the collocated scans on that day,
# we make one more request:
r3 = requests.get(day["URL"])
scanData = r3.json()["VDS"]

# scanData contains URIs for getting all the collocated Odin/SMR scans for
# 2012-09-15, as well as the data from MLS. As a final step, let"s request
# the latter for the first of the collocated scans (index 0 of scanData) for
# our chosen frequency mode, species, instrument and day. For MLS and O3, the
# final key is "URL-mls-O3". Refer to the VDS documentation or inspect the JSON
# object to find the key appropriate to your use case:
r4 = requests.get(scanData[0]["URLS"]["URL-mls-O3"])
mlsData = r4.json()

# Now we have the data at hand and can proceed with crunching it!
