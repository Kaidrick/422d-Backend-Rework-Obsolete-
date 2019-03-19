from core.request.api.api_debug import RequestApiLoadString
from core.request.miz.dcs_player import RequestPlayerInfo, DcsPlayer
from core.request.miz.dcs_env import env_player_dict, valid_group_id
from core.request.miz import dcs_env as db
import core.data_interface as cdi
import json

player_pref_data = 'data/ucid_settings.json'


def find_ucid_by_group_id(group_id):  # take group id, find ucid?
    if valid_group_id(group_id):
        group_player_name = db.env_group_dict[group_id].lead['player_name']
        ucid = env_player_dict[group_player_name].ucid
        return ucid
    else:
        return None


def find_player_preferences_by_group_id(group_id):  # env_group_dict is delayed, find in the file?
    # group_player_name = env_group_dict[group_id].lead['player_name']
    if valid_group_id(group_id):
        ucid = cdi.active_players_by_group_id(group_id).ucid  # find_ucid_by_group_id(group_id)
        with open(player_pref_data, 'r') as f_obj:
            ucid_setting_kv_dict = json.load(f_obj)
            pref = {
                'lang': ucid_setting_kv_dict[ucid]['lang'],
                'unit': ucid_setting_kv_dict[ucid]['unit']
            }
        return pref
    else:  # not active in game
        return None


def set_player_preference_lang(ucid, language):  # radio pull this method, by groupId?
    # how to know what ucid corresponds to this groupId? matching player name
    with open(player_pref_data, 'r+') as f_obj:
        ucid_setting_kv_dict = json.load(f_obj)
        ucid_setting_kv_dict[ucid]['lang'] = language
        ucid_setting_kv_dict[ucid]['lang_on_ip'] = False
        f_obj.seek(0)
        json.dump(ucid_setting_kv_dict, f_obj)
        f_obj.truncate()


def set_player_preference_unit(ucid, unit):  # radio pull this method
    with open(player_pref_data, 'r+') as f_obj:
        ucid_setting_kv_dict = json.load(f_obj)
        ucid_setting_kv_dict[ucid]['unit'] = unit
        f_obj.seek(0)
        json.dump(ucid_setting_kv_dict, f_obj)
        f_obj.truncate()


def get_player_preference_settings():  # FIXME: don't i/o file every second!
    # print(env_group_dict)
    all_connected_players = RequestPlayerInfo().send()
    # print(all_connected_players)
    if all_connected_players:
        file_name = 'data/ucid_settings.json'
        with open(file_name, 'r+') as f_obj:
            ucid_setting_kv_dict = json.load(f_obj)

            for ucid, player_info in all_connected_players.items():
                ipaddr = player_info['ipaddr']
                player_name = player_info['name']  # current name for this player
                net_id = player_info['playerID']

                new_player = DcsPlayer(ucid, ipaddr, net_id=net_id, name=player_name)

                if ucid in ucid_setting_kv_dict.keys():  # existing user
                    new_player.language = ucid_setting_kv_dict[ucid]['lang']
                    new_player.preferred_system = ucid_setting_kv_dict[ucid]['unit']
                    try:
                        new_player.lang_on_ip = ucid_setting_kv_dict[ucid]['lang_on_ip']
                    except KeyError:
                        ucid_setting_kv_dict[ucid]['lang_on_ip'] = False
                        new_player.lang_on_ip = ucid_setting_kv_dict[ucid]['lang_on_ip']

                else:  # new user, add preference? set default?
                    init_lang = RequestApiLoadString(f'return net.get_player_info({net_id}).lang').send()

                    print(f"New player [{player_name}]{new_player}({ucid}) using {init_lang} client has joined.")

                    # print("debug info", "player_preference.py", "ln 88", "init_lang: ", init_lang)
                    # init_lang = 'en'
                    supported_lang = ['cn', 'en', 'jp']
                    if init_lang not in supported_lang:
                        init_lang = 'en'

                    if init_lang == 'cn':
                        init_system = 'metric'
                    else:
                        init_system = 'imperial'

                    new_player.language = init_lang
                    new_player.preferred_system = init_system
                    new_player.lang_on_ip = True
                    new_player.player_id = net_id

                    ucid_setting_kv_dict[ucid] = {
                        'lang': init_lang,
                        'lang_on_ip': True,
                        'unit': init_system,
                        'player_id': net_id
                    }

                env_player_dict[player_name] = new_player
                cdi.player_net_config_by_ucid[ucid] = new_player

            f_obj.seek(0)
            json.dump(ucid_setting_kv_dict, f_obj)
            f_obj.truncate()
