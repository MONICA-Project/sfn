# convert_to_meter.py
"""Helper function to convert the distance between 2 geo point into metre."""
__version__ = '0.1'
__author__ = 'Hajar Sadeghi (KU)'

import math


def convert_to_meter(lat1, lon1, lat2, lon2):  # generally used geo measurement function
    r = 6378.137   # Radius of earth in KM
    d_latitude = lat2 * math.pi / 180 - lat1 * math.pi / 180
    d_longitude = lon2 * math.pi / 180 - lon1 * math.pi / 180
    a = math.sin(d_latitude/2) * math.sin(d_latitude/2) + math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) \
        * math.sin(d_longitude/2) * math.sin(d_longitude/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = r * c
    return d * 1000  # meters
