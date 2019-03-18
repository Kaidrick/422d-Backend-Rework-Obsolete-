from core.request.miz.dcs_request import RequestHandle, RequestDcs
import math
import numpy as np


class WxType:
	WX_AIRPORT = "wx_all_airport"  # nearest airport
	WX_OWNER = "wx_owner"  # weather data at unit position
	WX_SPEC = "wx_spec"  # weather data at a specific 3d point?

# player click on radio item to send a pull
# the pull asks for weather info
# query dcs for weather info
# send weather info as a dcs message to player


class WxStation:
	Caucasus = {}

	Nevada = {}

	PersianGulf = {}

# design a ATIS broadcast system: this system should be only be available at occupied airport?
# should be a radio broadcasting rather than trigger message, so its a request action



def unit_vector(vector):
	return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
	v1_u = unit_vector(v1)
	v2_u = unit_vector(v2)
	return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def get_wind_direction(t_v, mode='rad', ncorr=0):  # default to no north correction, true wind direction
	# wind direction --> the direction wind is blowing from
	# that is the opposite direction of wind vector itself
	dx = -t_v[1]
	dy = -t_v[0]
	hdg = 0

	if dx == 0 and dy == 0:
		hdg = math.pi * 2
	elif dx == 1 and dy == 0:
		hdg = math.pi / 2
	elif dx == 0 and dy == -1:
		hdg = math.pi
	elif dx == -1 and dy == 0:
		hdg = (3 / 2) * math.pi
	else:
		base = math.atan(math.fabs(dx) / math.fabs(dy))
		if dx > 0 and dy > 0:
			hdg = base
		elif dx > 0 and dy < 0:
			hdg = math.pi - base
		elif dx < 0 and dy < 0:
			hdg = math.pi + base
		elif dx < 0 and dy > 0:
			hdg = math.pi * 2 - base

	# check to avoid negative or over-360 heading value
	m_hdg = hdg + ncorr
	if m_hdg > math.pi * 2:
		m_hdg = m_hdg - math.pi * 2
	elif m_hdg < 0:
		m_hdg = math.pi * 2 + m_hdg

	if mode == 'deg':
		return np.rad2deg(m_hdg)
	elif mode == 'rad':
		return m_hdg


class RequestDcsWeather(RequestDcs):  # retrieve weather info on all registered points?
	# TODO: overload with loc or list of loc
	def __init__(self, loc_list):
		super().__init__(RequestHandle.QUERY)
		self.type = "weather"
		self.content = loc_list
		# loc is a dict: {'x': 12436547, 'y': 283, 'z': -3613645}


def get_2d_mag(vector_tuple):
	a, b = vector_tuple
	mag = math.sqrt(a ** 2 + b ** 2)
	return mag


def get_unit_heading():
	return None


def get_sea_level_pressure(altitude, pressure, temperature):
	P = pressure
	T = temperature
	h = altitude
	K = 273.15
	psl = P * (1 - 0.0065 * h / (T + 0.0065 * h + K)) ** -5.257
	return psl


def parse_wx(wx):  # TODO: overload to parse multiple wx data
	pressure = wx['press']  # this is probably QFE
	temperature = wx['temp']
	msl_pressure = wx['msl_press']
	msl_temperature = wx['msl_temp']

	surface_pressure = wx['surface_press']
	surface_temperature = wx['surface_tmp']

	wind = wx['wind']  # a dict
	# wind_turbulence = wx['wind_tur']  # a dict
	north_correction = wx['ncorr']
	point_location = wx['wx_loc']  # dict

	# read wind speed and direction
	# check if wind is 0
	# check if wind_turbulence is 0

	if wind['x'] == 0 and wind['y'] == 0 and wind['z'] == 0:  # wind is invalid
		wind = wx['wind_tur']
	else:  # wind is valid
		wind = wx['wind']

	wind_vector = (wind['z'], wind['x'])

	# wind speed
	wind_speed = get_2d_mag(wind_vector)

	# wind direction
	wind_direction = np.rad2deg(get_wind_direction(wind_vector, ncorr=0))
	# magnetic wind direction
	mag_wind_direction = np.rad2deg(get_wind_direction(wind_vector, ncorr=north_correction))  # but this can be negative?

	temperature_celsius = temperature - 273.15
	temperature_fahrenheit = (temperature - 273.15) * 9 / 5 + 32

	# qfe = pressure / 100  # pressure at this point in hP
	# fe = (point_location['y']) * 3.28084  # field elevation in feet, TODO: assuming airfield is above sea level
	# r_mb = fe / 27

	# qnh_hp = qfe + r_mb  # in hP
	# print(point_location['y'])

	# qnh_hp = get_sea_level_pressure(point_location['y'], qfe, temperature)

	# qnh_inhg = qnh_hp * 0.029530

	qnh_hp = msl_pressure / 100  # pressure at mean sea level
	qnh_inhg = msl_pressure * 0.00029530

	# QFE is always the pressure at the land height of a point
	qfe_hp = surface_pressure / 100
	qfe_inhg = surface_pressure * 0.00029530
	surface_temp_celsius = surface_temperature - 273.15
	surface_temp_fahrenheit = (surface_temperature - 273.15) * 9 / 5 + 32

	pressure_hp = pressure / 100  # pressure outside
	pressure_inhg = pressure * 0.00029530  # pressure outside in inHg
	wind_kt = wind_speed * 1.94384

	p_wx = {
		'wind': wind_speed,
		'wind_kt': wind_kt,
		'wind_dir': wind_direction,
		'ncorr': north_correction,
		'mag_wind_dir': mag_wind_direction,

		# temperatures
		'oat_celsius': temperature_celsius,
		'oat_fahrenheit': temperature_fahrenheit,
		'qfe_celsius': surface_temp_celsius,
		'qfe_fahrenheit': surface_temp_fahrenheit,

		# air pressures
		'out_pres': pressure_hp,
		'out_pres_inhg': pressure_inhg,
		'qnh_hp': qnh_hp,  # assuming this point is airport
		'qnh_inhg': qnh_inhg,  # assuming this point is airport
		'qfe_hp': qfe_hp,
		'qfe_inhg': qfe_inhg,
	}

	return p_wx
