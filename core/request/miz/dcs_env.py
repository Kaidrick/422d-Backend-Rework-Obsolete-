# this is a file that contains all the dicts that may be accessed by all other file
import gettext
import core.data_interface as cdi
env_group_dict = {}  # contains all group information: group_id, group_object <--pairs()
env_group_dict_by_name = {}
env_group_radio_dict = {}  # contains all radio items for groups
env_player_dict = {}  # contains all players
env_player_dict_by_group_id = {}
airbase_dict = {}  # contains all airbase information
airbase_pos_rev_dict = {}  # a reversed search table not sure if useful
theatre = ""
env_static_objects = {}


class Side:
    NEUTRAL = 0
    RED = 1
    BLUE = 2


class SurfaceType:
    LAND = 1
    SHALLOW_WATER = 2
    WATER = 3
    ROAD = 4
    RUNWAY = 5


def valid_group_id(group_id):
    try:
        for key, value in cdi.active_players_by_group_id.items():
            # print(key)
            if key == group_id:
                # print(cdi.active_players_by_group_id[key])
                return True
        # after loop no return
        return False
    except KeyError:
        print("key error")
        return False

    # if group_id in cdi.active_players_by_group_id.keys():
    #     # print(group_id, env_group_dict[group_id].__dict__)
    #     # print(cdi.active_players_by_group_id[group_id].language)
    #     print("so it's true?")
    #     return True
    # else:
    #     return None


def valid_radio_group_id(group_id):
    if group_id in env_group_radio_dict.keys():
        return True
    else:
        return None


def dcs_message_format(message):
    return message.lstrip('\n').rstrip('\n')


def set_msg_locale(locale, mo_name):
    if locale == 'en':
        _ = gettext.gettext
        return _
    else:  # for other locales, say cn
        this_locale = gettext.translation(mo_name, localedir='locale', languages=[locale])
        this_locale.install()
        _ = this_locale.gettext
        return _


def search_localized_string(string, locale, mo_file):
    _ = set_msg_locale(locale, mo_file)
    return _(string)


def filter_none_value(kn_dict):
    clean_dict = {}
    for key, value in kn_dict.items():
        if value:  # not None value
            clean_dict[key] = value

    return clean_dict


def bake_lua_object_by_runtime_id(runtime_id):  # 33555712
    lua_tbl = f"""{{['id_'] = {runtime_id},}}"""
    return lua_tbl
