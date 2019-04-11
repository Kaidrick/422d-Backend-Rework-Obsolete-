from core.request.exp.export_request import RequestExport, RequestExportHandle
import core.data_interface as cdi
from core.request.miz.dcs_debug import RequestDcsDebugCommand


class ExportDataType:
    UNITS = "units"
    BALLISTIC = "ballistic"
    AIRDROMES = "airdromes"
    OMNI = "omni"  # combined units and ballistic in one batch


class RequestExportData(RequestExport):
    def __init__(self):
        super().__init__(handle=RequestExportHandle.QUERY)


class RequestExportUnitsData(RequestExportData):
    def __init__(self):
        super().__init__()
        self.type = ExportDataType.UNITS


class RequestExportBallisticData(RequestExportData):
    def __init__(self):
        super().__init__()
        self.type = ExportDataType.BALLISTIC


class RequestExportAirdromesData(RequestExportData):
    def __init__(self):
        super().__init__()
        self.type = ExportDataType.AIRDROMES


class RequestExportOmniData(RequestExportData):
    def __init__(self):
        super().__init__()
        self.type = ExportDataType.OMNI


class ExportPlayerData:
    def __init__(self, runtime_id, unit_data):
        self.runtime_id = runtime_id[3:]
        self.player_name = unit_data['UnitName']
        self.player_group_name = unit_data['GroupName']
        self.unit_type = unit_data['Name']
        self.unit_wsType = unit_data['Type']
        self.unit_pos = unit_data['Position']
        self.unit_ll = unit_data['LatLongAlt']
        self.unit_att = {
            'pitch': unit_data['Pitch'],
            'bank': unit_data['Bank'],
            'heading': unit_data['Heading'],
        }
        self.unit_coalition = unit_data['Coalition']  # blue - Enemies, red - ?
        self.unit_country = unit_data['Country']
        self.unit_flags = unit_data['Flags']
        self.group_id = RequestDcsDebugCommand(f"return Group.getByName('{self.player_group_name}'):getID()", True).send()
        # generate group id reference
        self.unit_id = 0
        self.player_id = cdi.player_net_config_by_name[self.player_name]['player_id']
        self.ucid = cdi.player_net_config_by_name[self.player_name]['ucid']
        self.ipaddr = cdi.player_net_config_by_name[self.player_name]['ipaddr']
        self.language = cdi.player_net_config_by_name[self.player_name]['language']
        self.preferred_system = cdi.player_net_config_by_name[self.player_name]['preferred_system']

        cdi.active_players_by_group_id[self.group_id] = self
        # data that will be needed but cannot be exported are:
        # velocity?
        # callsign, maybe?
        # fuel
        # north correction
        # ammo

    def update(self, update_data):
        self.unit_pos = update_data['Position']
        self.unit_ll = update_data['LatLongAlt']
        self.unit_att = {
            'pitch': update_data['Pitch'],
            'bank': update_data['Bank'],
            'heading': update_data['Heading'],
        }
        self.unit_flags = update_data['Flags']

        cdi.active_players_by_group_id[self.group_id] = self


def update_dcs_data():
    units = RequestExportUnitsData().send()
    # check if this unit is a player controlled unit
    check_dt = cdi.active_players.copy()

    dt_name = []
    for unit_id_name, unit_data in units.items():  # map updated data to dictionary
        if unit_data['Flags']['Human'] is True:
            # check if unit already in cdi
            player_name = unit_data['UnitName']
            dt_name.append(player_name)
            if player_name not in cdi.active_players.keys():
                check_dt[player_name] = ExportPlayerData(unit_id_name, unit_data)
            else:  # player data is already exist, only updated data, don't create new object
                dt = check_dt[player_name]
                dt.update(unit_data)

        # else:  # unit is either invalid or AI unit or static
        #     if 'Name' in unit_data:  # at lease a valid object
        #         cdi.export_units[unit_id_name] = unit_data

    # if name not in updated name, del
    for unit_id_name in cdi.active_players.keys():  # for each key name
        if unit_id_name not in dt_name:  # if not in dt name
            group_id = check_dt.group_id
            del cdi.active_players_by_group_id[group_id]
            del check_dt[unit_id_name]  # del entry

    cdi.active_players = check_dt
    # exported units might not have Name(which is the unit type name), UnitName, GroupName

    # print(cdi.active_players_by_group_id)
    # print(cdi.active_players)


if __name__ == '__main__':
    import time
    while True:
        t = RequestExportUnitsData().send()
        for k, v in t.items():
            print(k, v)

        time.sleep(3)


