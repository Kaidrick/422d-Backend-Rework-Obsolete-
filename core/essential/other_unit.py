import time
import core.utility.data_parsing as parse


class OtherUnits:  # AI units and static objects?
    def __init__(self, runtime_id, unit_data):
        self.runtime_id = runtime_id[3:]

        # FIXME: consider the need to query the id data of a group added dynamically by script?
        if 'UnitName' in unit_data.keys():
            self.unit_name = unit_data['UnitName']
        if 'GroupName' in unit_data.keys():
            self.group_name = unit_data['GroupName']

        self.unit_type = unit_data['Name']
        self.unit_wsType = unit_data['Type']
        self.unit_coalition = unit_data['Coalition']  # blue - Enemies, red - ?
        self.unit_country = unit_data['Country']

        # init record field
        self.recent_pos = [unit_data['Position']]  # keep 10 recent position for calculation
        self.recent_pos_time = [time.time()]  # 10 timestamp corresponding to recent position

        # Data to keep updated
        self.unit_pos = unit_data['Position']
        self.unit_ll = unit_data['LatLongAlt']
        self.unit_att = {
            'pitch': unit_data['Pitch'],
            'bank': unit_data['Bank'],
            'heading': unit_data['Heading'],
        }
        self.unit_flags = unit_data['Flags']

        # data that will be needed but cannot be exported are:
        # velocity?
        # callsign, maybe?
        # fuel
        # north correction
        # ammo

    def update(self, update_data):
        # record pos data
        parse.record_position_time_pair(
            update_data['Position'], self.recent_pos, self.recent_pos_time
        )

        self.unit_pos = update_data['Position']
        self.unit_ll = update_data['LatLongAlt']
        self.unit_att = {
            'pitch': update_data['Pitch'],
            'bank': update_data['Bank'],
            'heading': update_data['Heading'],
        }
        self.unit_flags = update_data['Flags']
