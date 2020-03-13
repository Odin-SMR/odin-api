import requests

API_ROOT = "http://odin.rss.chalmers.se/rest_api/v5"
AREA_ENDPOINT = "/level2/{project}/area?{parameters}"


def load_equatorial_ozone(start_date, end_date, project="ALL-Strat-v3.0.0"):
    """Function for getting ozone data from the Odin REST API"""
    # Set up parameters:
    # Product from /level2/{project}/products/ with spaces replaced by %20:
    product = "product=O3%20%2F%20545%20GHz%20%2F%2020%20to%2085%20km"

    # Need only specify latitude limits:
    area = "&min_lat=-5&max_lat=5"

    # Altitude in meters:
    altitude = "&min_altitude=0&max_altitude=85000"

    # Period set from input to function:
    period = "&start_time={0}&end_time={1}".format(start_date, end_date)

    # Concatenate parameters:
    parameters = product + area + altitude + period

    # Construct request URL:
    request_url = API_ROOT + AREA_ENDPOINT.format(project=project,
                                                  parameters=parameters)
    # Get data:
    response = requests.get(request_url)

    # Return data:
    return response.json()
