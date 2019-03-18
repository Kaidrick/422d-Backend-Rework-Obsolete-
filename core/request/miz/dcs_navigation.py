import math
import gettext
import numpy as np
from scipy.spatial.distance import cdist
from core.request.miz.dcs_env import airbase_dict
# player navigation assist
# find the distance and course to one aiport
# what does python need to know: where is player, where is point, aircraft heading, speed

# what to produce: left or right? what heading? how long? keep tracking until arrive?
# then send message to player

# get the position of the player:
"""
new_group = DcsGroup()  # group table
		new_group.category = group['category']
		new_group.coalition = group['coalition']
		new_group.id = group['id']
		new_group.name = group['name']
		new_group.size = group['size']
		new_group.lead = group['units'][0]
		new_group.lead_pos = group['units'][0]['pos']
"""


def set_msg_locale(locale):
	if locale == 'en':
		_ = gettext.gettext
		return _
	else:  # for other locales, say cn
		this_locale = gettext.translation('dcs_navigation', localedir='locale', languages=[locale])
		this_locale.install()
		_ = this_locale.gettext
		return _


def get_2d_xy_dist(pos_1, pos_2):
	dx = pos_1['x'] - pos_2['x']
	dz = pos_1['z'] - pos_2['z']
	dist = math.sqrt(dx ** 2 + dz ** 2)
	return dist


def get_dir_vector(pos_1, pos_2):
	dx = pos_2['x'] - pos_1['x']
	dz = pos_2['z'] - pos_1['z']
	return (dx, dz)


def vec2hdg(t_v, mode='rad', ncorr=0):
	dx = t_v[1]
	dy = t_v[0]
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

	m_hdg = hdg + ncorr
	if m_hdg > math.pi * 2:
		m_hdg = m_hdg - math.pi * 2
	elif m_hdg < 0:
		m_hdg = math.pi * 2 + m_hdg

	if mode == 'deg':
		return np.rad2deg(m_hdg).round()
	elif mode == 'rad':
		return hdg


# receive a pull from a player
# this pull wants navigation assist to nearest airport?

# find nearest airport?
# find 5 nearest airport?
# as the player keeps flying, does the list of 5 nearest airport changes?

def find_nearest_airbase(pos):  # pos is the position of the pull group lead
	ab_name_idx = []
	ab_pos_idx = []
	for airbase_name, airbase_info in airbase_dict.items():  # initialized when program starts
		ab_pos = airbase_info.pos  # get airbase position
		ab_name_idx.append(airbase_name)
		ab_pos_idx.append([ab_pos['z'], ab_pos['x']])

	a = np.array([[pos['z'], pos['x']]])
	others = np.array(ab_pos_idx)
	distances = cdist(a, others)
	min_dist = others[distances.argmin()]
	for idx, other in enumerate(others):
		if np.array_equal(min_dist, other):
			return ab_name_idx[idx]


def generate_mgrs_std(mgrs_dict):
	easting = mgrs_dict['Easting']
	northing = mgrs_dict['Northing']
	utmz = mgrs_dict['UTMZone']
	digraph = mgrs_dict['MGRSDigraph']

	mgrs_str = f"{utmz} {digraph} {easting} {northing}"
	return mgrs_str


def generate_ll_deg_min(latitude, longitude, altitude, unit='metric'):
	lat_deci, lat_int = math.modf(latitude)
	lon_deci, lon_int = math.modf(longitude)

	# remove negative sign if any
	lat_deg = np.abs(lat_int)
	lat_min = np.abs(lat_deci * 60)

	lon_deg = np.abs(lon_int)
	lon_min = np.abs(lon_deci * 60)

	if latitude >= 0:  # north
		lat_prefix = "N"
	else:  # south
		lat_prefix = "S"

	if longitude >= 0:  # east
		lon_prefix = "E"
	else:  # west
		lon_prefix = "W"

	lat_str = f"{lat_prefix}{lat_deg:.0f}°{lat_min:06.3f}"
	lon_str = f"{lon_prefix}{lon_deg:.0f}°{lon_min:06.3f}"
	alt_str = f"{altitude:.0f}"

	return [lat_str, lon_str, alt_str]



# if __name__ == '__main__':
# 	from client import *
# 	get_all_groups()
# 	# print(env_group_dict)
# 	init_airbases()
# 	group_id = 127
# 	group_127 = env_group_dict[group_id]
# 	lead_pos = group_127.lead['pos']
# 	lead_velocity = group_127.lead['velocity']
# 	airport_kobuleti = airbase_dict['Lochini']
# 	# print(lead_pos)
# 	# print(lead_velocity)
# 	# print(airport_kobuleti.pos)
# 	dist = get_2d_xy_dist(lead_pos, airport_kobuleti.pos)
# 	print(f"distance is {dist} meters")
# 	vtp = get_dir_vector(lead_pos, airport_kobuleti.pos)
# 	# print(vtp)
# 	target_heading = vec2hdg(vtp, mode='deg')
# 	velocity_dir = vec2hdg((lead_velocity['z'], lead_velocity['x']), mode='deg')
# 	print(target_heading)
# 	print(velocity_dir)
#
# 	print(find_nearest_airbase(lead_pos))
#
# 	# calculate distance and heading to Anapa
#
# 	# calculate left or right turn, what is the current hdg?



# ai route assignment
