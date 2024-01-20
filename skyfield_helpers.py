import datetime

from skyfield.api import load


def date_to_timescale_time(date):
    ts = load.timescale()
    if date is None:
        t = ts.now()
    elif isinstance(date, tuple):
        t = ts.utc(*date[:5])  # e.g. t = ts.utc(2023, 7, 17, 0, 0)
    elif isinstance(date, datetime.datetime):
        t = ts.utc(*date.timetuple()[:5])
    else:
        raise ValueError(type(date))
    return t


import os, sys

def get_file_path(path):
    if getattr(sys, 'frozen', False):
        file_path = os.path.join(sys._MEIPASS, path)
    else:
        file_path = path
    return file_path