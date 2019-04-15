import core.data_interface as cdi


def missile_get_position(wpn_object_id: str):
    q_str = wpn_object_id
    try:  # try get missile data
        missile = cdi.export_units[q_str]
    except KeyError:
        print(__file__, "class Missile def control", "missile does not exist in cdi")
        return None  # fail to get missile position, missile does not exist in mission
    else:
        return missile.unit_pos

