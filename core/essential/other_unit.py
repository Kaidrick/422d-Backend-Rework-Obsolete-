import time
import core.utility.data_parsing as parse
import core.data_interface as cdi


def parse_other_unit(group_id, group_name, coalition, category, unit_data):
    other = OtherUnit(group_id, group_name, coalition, unit_data)
    # print(other.unit_name, other.unit_type, other.unit_pos)
    return other


class OtherUnit:  # AI units and static objects?
    def __init__(self, group_id, group_name, coalition, unit_data):

        # FIXME: consider the need to query the id data of a group added dynamically by script?
        self.runtime_id = unit_data['runtime_id']
        # print(self.runtime_id)

        self.unit_name = unit_data['name']
        self.group_name = group_name

        self.unit_type = unit_data['type']
        self.unit_coalition = coalition  # blue - Enemies, red - ?
        self.unit_country = unit_data['country']

        self.fuel = unit_data['fuel']

        # init record field
        self.recent_pos = [unit_data['pos']]  # keep 10 recent position for calculation
        self.recent_pos_time = [time.time()]  # 10 timestamp corresponding to recent position

        # Data to keep updated
        self.unit_pos = unit_data['pos']
        self.unit_ll = unit_data['coord']['LL']
        self.unit_att = {  # FIXME
            'pitch': unit_data['att'],
            'bank': unit_data['att'],
            'heading': unit_data['att'],
        }

        self.group_id = group_id

        # data that will be needed but cannot be exported are:
        # velocity?
        # callsign, maybe?
        # fuel
        # north correction
        # ammo

    # def update(self, update_data):
    #     # record pos data
    #     parse.record_position_time_pair(
    #         update_data['Position'], self.recent_pos, self.recent_pos_time
    #     )
    #
    #     self.unit_pos = update_data['Position']
    #     self.unit_ll = update_data['LatLongAlt']
    #     self.unit_att = {
    #         'pitch': update_data['Pitch'],
    #         'bank': update_data['Bank'],
    #         'heading': update_data['Heading'],
    #     }
