"""
This file contains all the table used to I/O game data, such as active players or active missiles
"""

# active players --> miz env dependent: the mission env decides when a player is active and when a player is inactive
# through in-game events
active_players = {}  # indexed by player UCID
active_players_by_group_id = {}  # indexed by player group id
active_players_by_name = {}  # indexed by player name

# all playable units indexed by group id, group name and unit_name
playable_unit_info_by_name = {}  # indexed by unit name
playable_unit_info_by_group_id = {}  # indexed by group id
playable_unit_info_by_group_name = {}  # indexed by group name
