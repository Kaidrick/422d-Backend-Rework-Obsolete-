"""
This file implements the player class. It is used as the model for player and player statistics
A Player object should contain overall information about a player, such as language, preference, group_id and stats
"""
import time
import core.data_interface as cdi


def parse_player_units(export_data):
    """
    This method is used to find and parse player controlled unit in the Export output data.
    After pasring, it generate a new player object and pass the object to data interface
    :return:
    """
    for unit_id_name, unit_data in export_data.items():
        if unit_data['Flags']['Human'] is True:
            # check if it has a matching data from mission env


class Player:
    """
    Player model
    """
    def __init__(self, player_name, group_id, unit_name, runtime_id):
        self.runtime_id_name = runtime_id
        self.runtime_id = int(runtime_id[3:])

        self.player_stat = None
        self._airspace = None  # this should be a string, such as R-62
        self.marker_panels = []  # a list of marker panels, some of which need to be updated at an interval

        self.invisible_to_ai = None

        self.player_name = unit_data['UnitName']
        self.player_group_name = unit_data['GroupName']
        self.unit_type = unit_data['Name']
        self.unit_wsType = unit_data['Type']
        self.unit_coalition = unit_data['Coalition']  # blue - Enemies, red - ?
        self.unit_country = unit_data['Country']

        # Data to keep updated
        self.last_unit_pos = unit_data['Position']

        # init record field
        self.recent_pos = [unit_data['Position']]  # keep 10 recent position for calculation
        self.recent_pos_time = [time.time()]  # 10 timestamp corresponding to recent position

        self.unit_pos = unit_data['Position']
        self.unit_ll = unit_data['LatLongAlt']
        self.unit_att = {
            'pitch': unit_data['Pitch'],
            'bank': unit_data['Bank'],
            'heading': unit_data['Heading'],
        }
        self.unit_flags = unit_data['Flags']

        # Query group id
        self.group_id = group_id

        # generate group id reference
        # data should be indexed by UCID rather than name?

        self.net_id = cdi.player_net_config_by_name[self.player_name].net_id
        self.ipaddr = cdi.player_net_config_by_name[self.player_name].ipaddr
        self.language = cdi.player_net_config_by_name[self.player_name].language
        self.preferred_system = cdi.player_net_config_by_name[self.player_name].preferred_system
        self.ucid = cdi.player_net_config_by_name[self.player_name].ucid
        self.lang_on_ip = cdi.player_net_config_by_name[self.player_name].lang_on_ip

        cdi.active_players_by_group_id[self.group_id] = self
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name] = self
        # data that will be needed but cannot be exported are:
        # velocity?
        # callsign, maybe?
        # fuel
        # north correction
        # ammo

    def check_movement(self):
        if self.last_unit_pos != self.unit_pos:  # player's position has changed
            return True
        else:  # player's position has not changed
            return False

    def update(self, update_data):
        # record last position
        self.last_unit_pos = self.unit_pos

        # record pos data
        parse.record_position_time_pair(
            update_data['Position'], self.recent_pos, self.recent_pos_time
        )
        # self.recent_pos, self.recent_pos_time = parse.record_position_time_pair(
        #     update_data['Position'], self.recent_pos, self.recent_pos_time
        # )

        self.unit_pos = update_data['Position']
        self.unit_ll = update_data['LatLongAlt']
        self.unit_att = {
            'pitch': update_data['Pitch'],
            'bank': update_data['Bank'],
            'heading': update_data['Heading'],
        }
        self.unit_flags = update_data['Flags']

        # sync update active_players_by_group_id
        cdi.active_players_by_group_id[self.group_id].unit_pos = update_data['Position']
        cdi.active_players_by_group_id[self.group_id].unit_ll = update_data['LatLongAlt']
        cdi.active_players_by_group_id[self.group_id].unit_att = {
            'pitch': update_data['Pitch'],
            'bank': update_data['Bank'],
            'heading': update_data['Heading'],
        }
        cdi.active_players_by_group_id[self.group_id].unit_flags = update_data['Flags']
        cdi.active_players_by_group_id[self.group_id].recent_pos = self.recent_pos
        cdi.active_players_by_group_id[self.group_id].recent_pos_time = self.recent_pos_time

        # sync update active_players_by_unit_runtime_id
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_pos = update_data['Position']
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_ll = update_data['LatLongAlt']
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_att = {
            'pitch': update_data['Pitch'],
            'bank': update_data['Bank'],
            'heading': update_data['Heading'],
        }
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_flags = update_data['Flags']
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].recent_pos = self.recent_pos
        cdi.active_players_by_unit_runtime_id[self.runtime_id_name].recent_pos_time = self.recent_pos_time

        if self.check_movement():  # if player has moved
            sig_dt = {
                'initiator': self.runtime_id_name,
                'type': "distance",
                'player_name': self.player_name,
                'player_group_id': self.group_id,
            }
            sig.player_distance(sig_dt)

    def drop(self):  # drop player data from dictionary, used when player unit no longer exists in miz
        del cdi.active_players_by_group_id[self.group_id]
        del cdi.active_players_by_unit_runtime_id[self.runtime_id_name]

    def set_airspace(self, airspace_name):
        self._airspace = airspace_name

    def get_airspace(self):
        return self._airspace

    def get_player_language(self):
        return cdi.player_net_config_by_name[self.player_name].language

    def get_player_preferred_system(self):
        return cdi.player_net_config_by_name[self.player_name].preferred_system

    def read_player_stat(self):
        """
        Read player statistics from file
        :return:
        """
        pass

    def save_player_stat(self):
        """
        Save player statistics to file
        :return:
        """
        pass