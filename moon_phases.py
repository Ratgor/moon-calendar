import numpy as np

from skyfield.api import load
from skyfield.constants import ERAD
from skyfield.functions import angle_between, length_of
from skyfield.searchlib import find_maxima
from skyfield.framelib import ecliptic_frame

from skyfield_helpers import date_to_timescale_time, get_file_path

# === skyfield part ===

def get_moon_phase(date=None):

    # Create a timescale and ask the current time.
    t = date_to_timescale_time(date)

    # Load the JPL ephemeris DE421 (covers 1900-2050).
    eph = load(get_file_path('de421.bsp'))
    sun, moon, earth = eph['sun'], eph['moon'], eph['earth']

    # planets = load('de421.bsp')
    # earth, mars = planets['earth'], planets['mars']
    #
    # # What's the position of Mars, viewed from Earth?
    # astrometric = earth.at(t).observe(mars)
    # ra, dec, distance = astrometric.radec()
    #
    # print(ra)
    # print(dec)
    # print(distance)

    e = earth.at(t)
    _, slon, _ = e.observe(sun).apparent().frame_latlon(ecliptic_frame)
    _, mlon, _ = e.observe(moon).apparent().frame_latlon(ecliptic_frame)
    phase = (mlon.degrees - slon.degrees) % 360.0

    return phase

def get_moon_eclipses(date_from, date_to):

    eph = load('de421.bsp')
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    def f(t):
        e = earth.at(t).position.au
        s = sun.at(t).position.au
        m = moon.at(t).position.au
        return angle_between(s - e, m - e)

    f.step_days = 5.0

    ts = load.timescale()
    start_time = date_to_timescale_time(date_from)
    end_time = date_to_timescale_time(date_to)

    t, y = find_maxima(start_time, end_time, f)

    e = earth.at(t).position.m
    m = moon.at(t).position.m
    s = sun.at(t).position.m

    solar_radius_m = 696340e3
    moon_radius_m = 1.7371e6

    pi_m = np.arcsin(ERAD / length_of(m - e))
    pi_s = np.arcsin(ERAD / length_of(s - e))
    s_s = np.arcsin(solar_radius_m / length_of(s - e))

    pi_1 = 0.998340 * pi_m

    sigma = angle_between(s - e, e - m)
    s_m = np.arcsin(moon_radius_m / length_of(e - m))

    penumbral = sigma < 1.02 * (pi_1 + pi_s + s_s) + s_m
    partial = sigma < 1.02 * (pi_1 + pi_s - s_s) + s_m
    total = sigma < 1.02 * (pi_1 + pi_s - s_s) - s_m

    mask = penumbral | partial | total

    t = t[mask]
    penumbral = penumbral[mask]
    partial = partial[mask]
    total = total[mask]
    totality_rating = [0 + penumbral + partial + total]
    print(f"DEBUG: {len(t)} moon eclipses found in range from {start_time.utc_strftime()} to {start_time.utc_strftime()}: "
          f"dates {t.utc_strftime()}, totality rating {totality_rating}")

    return [(d, r) for d,r in zip(t.utc_strftime(), totality_rating)]
