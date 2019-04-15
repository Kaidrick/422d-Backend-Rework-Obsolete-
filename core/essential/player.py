"""
This file implements the player class. It is used as the model for player and player statistics
A Player object should contain overall information about a player, such as language, preference, group_id and stats
"""
import time
import core.data_interface as cdi
import numpy as np
import core.spark as spark


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

        self.player_stat = PlayerStats()
        self._airspace = None  # this should be a string, such as R-62
        self.marker_panels = []  # a list of marker panels, some of which need to be updated at an interval

        self.invisible_to_ai = None

        self.runtime_id = unit_data['runtime_id']
        self.runtime_id_name = 'id_' + str(self.runtime_id)

        self.player_name = unit_data['player_name']
        self.unit_name = unit_data['name']
        self.player_group_name = group_name
        self.unit_type = unit_data['type']
        self.unit_coalition = coalition  # blue - Enemies, red - ?
        self.unit_country = unit_data['country']

        self.fuel = unit_data['fuel']
        self.velocity = unit_data['velocity']

        # Data to keep updated
        self.last_unit_pos = unit_data['pos']

        self.move_dir = np.array([0, 0, 0])  # moving direction as vec3 in LO

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

    def hi_res(self):  # get accurate data from export
        # check if player exist as a valid id in cdi
        try:
            hi_res = cdi.export_omni[self.runtime_id_name]
        except KeyError:
            print("Unable to find player in export data")
            return None
        else:
            hi_res_data = {
                'pos': hi_res['Position'],
                'll': hi_res['LatLongAlt'],
                'hdg': hi_res['Heading'],
                'pitch': hi_res['Pitch'],
                'bank': hi_res['Bank']
            }
            return hi_res_data

    def update(self, update_data):
        self.last_unit_pos = self.unit_pos

        self.fuel = update_data['fuel']
        self.velocity = update_data['velocity']
        self.unit_pos = update_data['pos']
        self.unit_ll = update_data['coord']['LL']
        self.mgrs = update_data['coord']['MGRS']
        self.unit_att = {  # FIXME
            'pitch': update_data['att'],
            'bank': update_data['att'],
            'heading': update_data['att'],
        }

        # check if player has moved during the last simulation export
        if self.last_unit_pos != self.unit_pos:  # player's position has changed
            array_last_unit_pos = np.array(
                [
                    self.last_unit_pos['x'], self.last_unit_pos['y'], self.last_unit_pos['z']
                ]
            )
            array_unit_pos = np.array(
                [
                    self.unit_pos['x'], self.unit_pos['y'], self.unit_pos['z']
                ]
            )
            self.move_dir = array_unit_pos - array_last_unit_pos

            spk_dt = {
                'type': 'player_distance',
                'data': {
                    'runtime_id': self.runtime_id_name,
                    'player_name': self.player_name,
                    'sp': self.last_unit_pos,
                    'ep': self.unit_pos,
                    'move_dir': self.move_dir,
                    'self': self
                }
            }
            spark.player_distance(spk_dt)

        return self

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


class PlayerStats:
    def __init__(self):
        self.weapons_released = []
        self.airspace_routes = []

        self.sessions = []
