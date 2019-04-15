import core.data_interface as cdi


def unit_object_by_runtime_id_name(runtime_id_name):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id_name == runtime_id_name:
            return unit_obj

    # after search, none found
    return None


# get target position by runtime_id (int)
def get_target_position_lua_object(lua_object: dict):
    target_id_name = 'id' + lua_object['id']

    try:
        target = unit_object_by_runtime_id_name(target_id_name)
    except KeyError:  # chances are that target is not in cdi, thus not in mission anymore
        return None
    else:
        target_pos = target.unit_pos
        return target_pos, target

