import random

from utilities.main import database_connection, database_cursor

def swap_chars(s: str, count: int):
    print(count)
    end = len(s) - 1
    count = min(count, len(s) // 2)
    lst = list(s)

    for i in range(count):
        i = random.randint(0, end)
        j = random.randint(0, end)
        lst[i],lst[j] = lst[j],lst[i]
    print('before: ', s)
    print('after: ', lst)
    return "".join(lst)

def location_drift(longitude: float, latitude: float, max_drift: float):
    longitude += random.random() * max_drift
    latitude += random.random() * max_drift
    if longitude > 180: longitude = 180
    if latitude > 90: latitude = 90
    return longitude, latitude