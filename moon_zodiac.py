# https://forums.gentoo.org/viewtopic-p-8799546.html?sid=d931cb54290baff9f510a92aa3e60bf7#8799546
# https://forums.gentoo.org/viewtopic-p-8799546.html#8799546
# https://www.dropbox.com/scl/fi/qw1x2tsnzypaxsgrdw91w/hexagram_data.txt?rlkey=aw1nou400j8f45t52gse7mmty&dl=0

from skyfield_helpers import date_to_timescale_time, get_file_path

from skyfield.api import load
from skyfield.framelib import ecliptic_frame

planets = load('de421.bsp') # load a planetary ephemeris
moon = planets['moon'] # get the Moon object
earth = planets['earth'] # get the Earth object
ts = load.timescale() # load a timescale object
t = ts.now() # get the current time

# define a function that returns the ecliptic longitude of the Moon
def moon_longitude(t):
    e = earth.at(t) # get the position of the Earth at time t
    _, lon, _ = e.observe(moon).apparent().frame_latlon(ecliptic_frame) # get the ecliptic latitude and longitude of the Moon
    return lon # return the longitude

# define a list of zodiac signs and their symbols
signs = ['Aries ♈', 'Taurus ♉', 'Gemini ♊', 'Cancer ♋', 'Leo ♌', 'Virgo ♍', 'Libra ♎', 'Scorpio ♏', 'Sagittarius ♐', 'Capricorn ♑', 'Aquarius ♒', 'Pisces ♓']

# define a function that returns the zodiac sign and degree of a given ecliptic longitude
def zodiac_sign(lon):
    sign_index = int(lon.degrees // 30) # get the index of the sign by dividing the longitude by 30 degrees
    sign = signs[sign_index] # get the sign name and symbol
    degree = lon.degrees % 30 # get the degree within the sign by taking the remainder of dividing the longitude by 30 degrees
    return sign, degree # return the sign and degree

# define a function that reads a text file containing gate and line information and returns a dictionary with this information
def read_gates(filename):
    gates = {}
    with open(filename, 'r') as f:
        current_gate = None
        for line in f:
            if line.startswith('gate'):
                if current_gate is not None:
                    gates[current_gate] = gate_data
                gate_name, sign_name = line.strip().split(' = ')
                #print(f"Gate Name: {gate_name}, Sign Name: {sign_name}")
                current_gate = gate_name
                gate_data = {'sign': sign_name, 'lines': []}
            elif line.startswith('line'):
                line_name, coords = line.strip().split(' = ')
               # print(f"Line Name: {line_name}, Coords: {coords}")
                line_number = int(line_name.split('_')[1])
                coords = coords.replace('°', ' ').replace('Â', ' ').replace("'", ' ').replace('"', '').split(' - ')
                start_coords = coords[0]
                end_coords = coords[1]
                if '/' in start_coords:
                    start_signs = start_coords.split('/')
                    start_dms = [tuple(map(int, sign.split())) for sign in start_signs]
                else:
                    start_dms = tuple(map(int, start_coords.split()))
                if '/' in end_coords:
                    end_signs = end_coords.split('/')
                    end_dms = [tuple(map(int, sign.split())) for sign in end_signs]
                else:
                    end_dms = tuple(map(int, end_coords.split()))
                gate_data['lines'].append((line_number, start_dms, end_dms))
        if current_gate is not None:
            gates[current_gate] = gate_data
    return gates

# define a function that converts degrees, minutes, and seconds to decimal degrees
def dms_to_degrees(dms):
    d, m, s = dms
    return d + m / 60 + s / 3600

# read the gates from a text file (replace '/home/ethan/Documents/hexagram_data.txt' with the path to your text file)
gates = read_gates(get_file_path('./hexagram_data.txt'))


# get the ecliptic longitude of the Moon at the current time
lon = moon_longitude(t)
# get the zodiac sign and degree of the Moon at the current time
sign, degree = zodiac_sign(lon)
# convert the degree to degrees, minutes, and seconds
d, m, s = int(degree), int(degree * 60) % 60, int(degree * 3600) % 60


# find which gate and line corresponds to the current position of the Moon
current_gate = None
current_line = None
for gate_number, gate in gates.items():
    if gate['sign'] == sign.split(' ')[0]:
        print(f"Checking Gate {gate_number} ({gate['sign']})")
        for line_number, start_dms, end_dms in gate['lines']:
            start_degrees = dms_to_degrees(start_dms)
            end_degrees = dms_to_degrees(end_dms)
            if start_degrees <= degree < end_degrees:
                print(f"  Checking Line {line_number}: {start_degrees} - {end_degrees}")
                current_gate = gate_number
                current_line = line_number
                break

# print the result in a formatted way
if current_gate is not None and current_line is not None:
    print(f'The Moon is currently at {sign}, {d}°{m}\'{s}\", Gate {current_gate}, Line {current_line}')
else:
    print(f'The Moon is currently at {sign}, {d}°{m}\'{s}\"')


def get_moon_at_sign(date):
    t = date_to_timescale_time(date)

    # get the ecliptic longitude of the Moon at the current time
    lon = moon_longitude(t)
    # get the zodiac sign and degree of the Moon at the current time
    sign, degree = zodiac_sign(lon)
    # convert the degree to degrees, minutes, and seconds
    d, m, s = int(degree), int(degree * 60) % 60, int(degree * 3600) % 60

    return lon, sign, degree, d, m, s

