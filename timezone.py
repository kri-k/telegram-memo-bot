# -*- coding: utf-8 -*-

import datetime
import requests
import conf
from logger import logger


CACHE_DATE = None
CACHE_LIMIT_SIZE = 10000
CACHED_ADDRESSES = {}
CACHED_GEOPOS = {}


class TimeZone:
    def __init__(self, r):
        self.offset = r['rawOffset'] + r['dstOffset']
        self.tz_id = r['timeZoneId']
        self.tz_name = r['timeZoneName']

    def __str__(self):
        return '\n'.join((self.tz_id, self.tz_name))

    def get_current_time(self):
        ts = int(datetime.datetime.utcnow().timestamp()) + self.offset
        return datetime.datetime.fromtimestamp(ts).strftime('%d.%m.%Y %X')

    def get_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp + self.offset).strftime('%d.%m.%Y %X')

    def get_time_short(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp + self.offset).strftime('%d.%m %H:%M')


def geopos_to_key(lat, lng):
    return (_cut_geopos(str(lat)), _cut_geopos(str(lng)))


def get_timezone(geopos):
    _check_date()
    return _get_timezone_from_geopos(geopos)


def get_geopos_for_address(address):
    address = address.strip().lower()
    if address in CACHED_ADDRESSES:
        return CACHED_ADDRESSES[address]
    geopos = _request_geopos_for_address(address)
    if len(CACHED_ADDRESSES) == CACHE_LIMIT_SIZE:
        CACHED_ADDRESSES.popitem()
    CACHED_ADDRESSES[address] = geopos
    return geopos


def _get_timezone_from_geopos(key):
    if key in CACHED_GEOPOS:
        return CACHED_GEOPOS[key]
    tz = _request_timezone_for_geopos(key)
    if len(CACHED_GEOPOS) == CACHE_LIMIT_SIZE:
        CACHED_GEOPOS.popitem()
    CACHED_GEOPOS[key] = tz
    return CACHED_GEOPOS[key]


def _request(s):
    try:
        r = requests.get(s)
    except Exception:
        logger.exception('Cant connect to "{}"'.format(s))
        return None

    try:
        r = r.json()
    except Exception:
        logger.exception('Something went wrong while parsing JSON from "{}"'.format(s))
        return None

    if r['status'] != 'OK':
        logger.error('"{}" answer status is "{}"'.format(s, r['status']))
        return None

    return r


def _request_timezone_for_geopos(geopos):
    s = conf.GOOGLE_TIMEZONE_API_STR.format(*geopos, CACHE_DATE, conf.GOOGLE_TIMEZONE_API_KEY)
    r = _request(s)
    if r is None:
        return None
    return TimeZone(r)


def _request_geopos_for_address(address):
    s = conf.GOOGLE_GEOCODE_API_STR.format(address, conf.GOOGLE_GEOCODE_API_KEY)
    r = _request(s)
    if r is None:
        return None
    r = r['results'][0]['geometry']['location']
    return geopos_to_key(r['lat'], r['lng'])


def _cut_geopos(s):
    a, b = s.split('.')
    b = b[:3]
    return '.'.join((a, b))


def _check_date():
    global CACHE_DATE, CACHED_ADDRESSES, CACHED_GEOPOS
    d = datetime.datetime.utcnow().date()
    d, _ = str(datetime.datetime(d.year, d.month, d.day).timestamp()).split('.')
    if CACHE_DATE is None or CACHE_DATE != d:
        CACHE_DATE = d
        CACHED_ADDRESSES = {}
        CACHED_GEOPOS = {}


if __name__ == '__main__':
    pass
