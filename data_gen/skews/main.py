import random

from utilities.main import database_connection, database_cursor

def swap_chars(s: str, i: int, j: int):
    if len(s)-1 < j:
        return s
    lst = list(s)
    lst[i],lst[j] = lst[j],lst[i]
    return "".join(lst)

def location_drift(longitude: float, latitude: float, max_drift: float):
    longitude += random.random() * max_drift
    latitude += random.random() * max_drift
    if longitude > 180: longitude = 180
    if latitude > 90: latitude = 90
    return longitude, latitude