"""
This file contains all the table used to I/O game data, such as active players or active missiles
"""
from core.request.miz.dcs_debug import RequestDcsDebugCommand
import time

# Theatre
utc = {  # add this time to get UTC
    'Nevada': 8,
    'Caucasus': -3,
    'PersianGulf': -4
}
theatre = RequestDcsDebugCommand("return env.mission.theatre", True).send()
mission_start_time = RequestDcsDebugCommand("return env.mission.start_time", True).send()
mission_start_utc = mission_start_time + utc[theatre] * 3600
mission_start_real_world_time = time.ctime()

print(f"Initiate Backend For {theatre}, Mission Start Time: {mission_start_time / 3600:.2f} hour, "
      f"UTC: {mission_start_utc / 3600:.2f} hour")

# -----------------------------------------------------------------------------------------------------------

# active players --> miz env dependent: the mission env decides when a player is active and when a player is inactive
# through in-game events
active_players = {}  # indexed by player UCID

active_players_by_name = {}  # indexed by player name

# all playable units indexed by group id, group name and unit_name
playable_unit_info_by_unit_name = {}  # indexed by unit name
playable_unit_info_by_group_id = {}  # indexed by group id
playable_unit_info_by_group_name = {}  # indexed by group name

# AI Controlled Units
other_units_by_name = {}  # indexed by unit name

# player preferences
player_net_config_by_ucid = {}

# -----------------------------------------------------------------------------------------------------------
# Export Data for look up
export_units = {}
export_ballistic = {}
export_airdromes = {}

export_omni = {}

# -----------------------------------------------------------------------------------------------------------
# Data Models
active_munition = {}

# -----------------------------------------------------------------------------------------------------------
# Other useful thingy
weapon_shot_event_log = {}  # del entry when a search is done
dead_other_units = {}  #

# plugins
d_atis = {}  # airport_atis
# cdi.d_atis[ab] = {
#     'info_ident': info_letter,
#     'time_string': timeString,
#     'mag_wind_dir': mag_wind_dir,
#     'wind_kt': wind_kt,
#     'wind_mps': wind,
#     'oat': oat,
#     'altimeter': qnh_inhg,
#     'altimeter_hp': qnh_hp,
#     'rw_in_use': use_rw,
# }

tanker_sta = {}  # dispatch_tankers
# tanker_data = {
#     'type': ac_type,
#     'on_track_spd': spd,
#     'alt': alt,
#     'chn': chn,
#     'mode': chn_mode,
#     'ident': ident,  # identifier of the beacon
#     'freq': freq,
#     'callsign': callsign
# }
