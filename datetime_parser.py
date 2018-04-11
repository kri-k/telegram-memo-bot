# -*- coding: utf-8 -*-

import re


def after_n_minutes(match, utc_timestamp):
    t = match.group(0)
    if t is None or len(t) == 0:
        return None
    t = match.group(1)
    if t is None or len(t) == 0:
        t = '1'
    return utc_timestamp + int(t) * 60


def after_n_hours(match, utc_timestamp):
    t = match.group(0)
    if t is None or len(t) == 0:
        return None
    t = match.group(1)
    if t is None or len(t) == 0:
        t = '1'
    return utc_timestamp + int(t) * 3600


def data_time(match, utc_timestamp):
    return None


RE_HANDLES = [
    (re.compile('^.*через\s*(\d*)\s*(?:минуту|минуты|минут|мин).*$', re.U | re.I), after_n_minutes),
    (re.compile('^.*через\s*(\d*)\s*(?:часов|часа|час).*$', re.U | re.I), after_n_hours),
    (re.compile('^(\d\d.\d\d.\d\d\d\d)\s*$', re.U | re.I), data_time),
]


def get_timestamp(msg, utc_timestamp):
    time = None
    for r, f in RE_HANDLES:
        m = r.match(msg)
        if m is not None:
            time = f(m, utc_timestamp)
            if time is not None:
                break
    if time is None:
        return None
    return time


if __name__ == '__main__':
    pass
