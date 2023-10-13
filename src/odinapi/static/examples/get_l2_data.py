import requests
from typing import Tuple

API_ROOT = "http://odin.rss.chalmers.se/rest_api/v5"
PROJECTS_ENDPOINT = "/level2/projects/"
PRODUCTS_ENDPOINT = "/level2/{project}/products/"
LOCATIONS_ENDPOINT = "/level2/{project}/locations"
AREA_ENDPOINT = "/level2/{project}/area"
DATE_ENDPOINT = "/level2/{project}/{date}/"


def get_projects() -> dict:
    """Function for getting projects from the Odin REST API"""

    # Construct request URI:
    request_url = API_ROOT + PROJECTS_ENDPOINT

    # Get data:
    response = requests.get(request_url)

    # Return data:
    return response.json()


def get_products(project: str = "ALL-Strat-v3.0.0") -> dict:
    """Function for getting products from the Odin REST API"""

    # Construct request URI:
    request_url = API_ROOT + PRODUCTS_ENDPOINT.format(project=project)

    # Get data:
    response = requests.get(request_url)

    # Return data:
    return response.json()


def get_location(
    start_date: str,
    end_date: str,
    project: str = "ALL-Strat-v3.0.0",
    product: str = "O3 / 545 GHz / 20 to 85 km",
    location: Tuple[float, float] = (90, 0),
    radius: float = 2600,
    min_altitude: float = 20000,
    max_altitude: float = 85000,
) -> list:
    """Function for getting data for a location from the Odin REST API"""

    # Set up parameters:
    parameters: dict[str, str | float] = {
        "product": product,
        "location": "{}, {}".format(*location),
        "radius": radius,
        "min_altitude": min_altitude,
        "max_altitude": max_altitude,
        "start_time": start_date,
        "end_time": end_date,
    }

    # Construct request URI:
    request_url = API_ROOT + AREA_ENDPOINT.format(project=project)

    # Get data:
    response = requests.get(request_url, params=parameters)
    data = [response.json()]

    # Note that this endpoint is paginated,
    # and the loop below retrieves data from all pages:
    while "next" in response.links:
        response = requests.get(response.links["next"]["url"])
        data.append(response.json())

    return data


def get_area(
    start_date: str,
    end_date: str,
    project: str = "ALL-Strat-v3.0.0",
    product: str = "O3 / 545 GHz / 20 to 85 km",
    min_lat: float = -5,
    max_lat: float = 5,
    min_lon: float = 0,
    max_lon: float = 360,
    min_altitude: float = 20000,
    max_altitude: float = 85000,
) -> list:
    """Function for getting data for an area from the Odin REST API"""

    # Set up parameters:
    parameters: dict[str, float | str] = {
        "product": product,
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
        "min_altitude": min_altitude,
        "max_altitude": max_altitude,
        "start_time": start_date,
        "end_time": end_date,
    }

    # Construct request URI:
    request_url = API_ROOT + AREA_ENDPOINT.format(project=project)

    # Get data:
    response = requests.get(request_url, params=parameters)
    data = [response.json()]

    # Note that this endpoint is paginated,
    # and the loop below retrieves data from all pages:
    while "next" in response.links:
        response = requests.get(response.links["next"]["url"])
        data.append(response.json())

    return data


def get_date(
    date: str,
    project: str = "ALL-Strat-v3.0.0",
    product: str = "O3 / 545 GHz / 20 to 85 km",
    min_altitude: float = 20000,
    max_altitude: float = 85000,
) -> dict:
    """Function for getting data for a single date from the Odin REST API"""

    # Set up parameters:
    parameters: dict[str, str | float] = {
        "product": product,
        "min_altitude": min_altitude,
        "max_altitude": max_altitude,
    }

    # Construct request URI:
    request_url = API_ROOT + DATE_ENDPOINT.format(project=project, date=date)

    # Get data:
    response = requests.get(request_url, params=parameters)

    # Return data:
    return response.json()
