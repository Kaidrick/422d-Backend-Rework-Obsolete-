"""
This file implements the player class. It is used as the model for player and player statistics
A Player object should contain overall information about a player, such as language, preference, group_id and stats
"""
import time
import core.data_interface as cdi


def parse_player_unit(group_id, group_name, coalition, category, unit_data):
    """
    This method is used to find and parse player controlled unit in the Export output data.
    After pasring, it generate a new player object and pass the object to data interface
    :return:
    """
    player = Player(group_id, group_name, coalition, unit_data)
    # print(player.player_name, player.unit_type, player.unit_pos)
    return player


class Player:
    """
    Player model
    """
    def __init__(self, group_id, group_name, coalition, unit_data):

        self.player_stat = None
        self._airspace = None  # this should be a string, such as R-62
        self.marker_panels = []  # a list of marker panels, some of which need to be updated at an interval

        self.invisible_to_ai = None

        self.runtime_id = unit_data['runtime_id']

        self.player_name = unit_data['player_name']
        self.unit_name = unit_data['name']
        self.player_group_name = group_name
        self.unit_type = unit_data['type']
        self.unit_coalition = coalition  # blue - Enemies, red - ?
        self.unit_country = unit_data['country']

        self.fuel = unit_data['fuel']

        # Data to keep updated
        self.last_unit_pos = unit_data['pos']

        # init record field
        self.recent_pos = [unit_data['pos']]  # keep 10 recent position for calculation
        self.recent_pos_time = [time.time()]  # 10 timestamp corresponding to recent position

        self.unit_pos = unit_data['pos']
        self.unit_ll = unit_data['coord']['LL']
        self.mgrs = unit_data['coord']['MGRS']
        self.unit_att = {  # FIXME
            'pitch': unit_data['att'],
            'bank': unit_data['att'],
            'heading': unit_data['att'],
        }
        # Query group id
        self.group_id = group_id

        # generate group id reference
        # data should be indexed by UCID rather than name?

        # search for player name
        for p_ucid, p_net_data in cdi.player_net_config_by_ucid.items():
            if p_net_data.name == self.player_name:
                self.net_id = p_net_data.net_id
                self.ipaddr = p_net_data.ipaddr
                self.language = p_net_data.language
                self.preferred_system = p_net_data.preferred_system
                self.ucid = p_net_data.ucid
                self.lang_on_ip = p_net_data.lang_on_ip

        # self.net_id = cdi.player_net_config_by_name[self.player_name].net_id
        # self.ipaddr = cdi.player_net_config_by_name[self.player_name].ipaddr
        # self.language = cdi.player_net_config_by_name[self.player_name].language
        # self.preferred_system = cdi.player_net_config_by_name[self.player_name].preferred_system
        # self.ucid = cdi.player_net_config_by_name[self.player_name].ucid
        # self.lang_on_ip = cdi.player_net_config_by_name[self.player_name].lang_on_ip
        #
        # cdi.active_players_by_group_id[self.group_id] = self
        # cdi.active_players_by_unit_runtime_id[self.runtime_id_name] = self

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

    # def update(self, update_data):
    #     # record last position
    #     self.last_unit_pos = self.unit_pos
    #
    #     # record pos data
    #     # parse.record_position_time_pair(
    #     #     update_data['Position'], self.recent_pos, self.recent_pos_time
    #     # )
    #     # self.recent_pos, self.recent_pos_time = parse.record_position_time_pair(
    #     #     update_data['Position'], self.recent_pos, self.recent_pos_time
    #     # )
    #
    #     self.unit_pos = update_data['Position']
    #     self.unit_ll = update_data['LatLongAlt']
    #     self.unit_att = {
    #         'pitch': update_data['Pitch'],
    #         'bank': update_data['Bank'],
    #         'heading': update_data['Heading'],
    #     }
    #
    #     # sync update active_players_by_group_id
    #     cdi.active_players_by_group_id[self.group_id].unit_pos = update_data['Position']
    #     cdi.active_players_by_group_id[self.group_id].unit_ll = update_data['LatLongAlt']
    #     cdi.active_players_by_group_id[self.group_id].unit_att = {
    #         'pitch': update_data['Pitch'],
    #         'bank': update_data['Bank'],
    #         'heading': update_data['Heading'],
    #     }
    #     cdi.active_players_by_group_id[self.group_id].unit_flags = update_data['Flags']
    #     cdi.active_players_by_group_id[self.group_id].recent_pos = self.recent_pos
    #     cdi.active_players_by_group_id[self.group_id].recent_pos_time = self.recent_pos_time
    #
    #     # sync update active_players_by_unit_runtime_id
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_pos = update_data['Position']
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_ll = update_data['LatLongAlt']
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_att = {
    #         'pitch': update_data['Pitch'],
    #         'bank': update_data['Bank'],
    #         'heading': update_data['Heading'],
    #     }
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].unit_flags = update_data['Flags']
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].recent_pos = self.recent_pos
    #     cdi.active_players_by_unit_runtime_id[self.runtime_id_name].recent_pos_time = self.recent_pos_time
    #
    #     if self.check_movement():  # if player has moved
    #         sig_dt = {
    #             'initiator': self.runtime_id_name,
    #             'type': "distance",
    #             'player_name': self.player_name,
    #             'player_group_id': self.group_id,
    #         }
    #         # spark.player_distance(sig_dt)

    # def drop(self):  # drop player data from dictionary, used when player unit no longer exists in miz
    #     del cdi.active_players_by_group_id[self.group_id]
    #     del cdi.active_players_by_unit_runtime_id[self.runtime_id_name]

    def set_airspace(self, airspace_name):
        self._airspace = airspace_name

    def get_airspace(self):
        return self._airspace

    # def get_player_language(self):
    #     return cdi.player_net_config_by_name[self.player_name].language
    #
    # def get_player_preferred_system(self):
    #     return cdi.player_net_config_by_name[self.player_name].preferred_system

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

    def drop_data(self):
        del cdi.active_players_by_name[self.player_name]
