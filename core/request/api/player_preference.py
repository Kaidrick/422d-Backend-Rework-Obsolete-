from core.request.api.api_debug import RequestApiLoadString
from core.request.miz.dcs_player import RequestPlayerInfo, DcsPlayer
from core.request.miz.dcs_env import env_player_dict, valid_group_id
from core.request.miz import dcs_env as db
import core.data_interface as cdi
import json
import requests
import urllib3
import http
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
                # ucid = player_info['ucid']
                new_player = DcsPlayer(ucid, ipaddr, net_id=net_id, name=player_name)

                if ucid in ucid_setting_kv_dict.keys():  # existing user
                    # print("found ucid-->" + ucid + ucid_setting_kv_dict[ucid]['lang'] + ucid_setting_kv_dict[ucid]['unit'])
                    new_player.language = ucid_setting_kv_dict[ucid]['lang']
                    new_player.preferred_system = ucid_setting_kv_dict[ucid]['unit']
                    try:
                        new_player.lang_on_ip = ucid_setting_kv_dict[ucid]['lang_on_ip']
                    except KeyError:
                        ucid_setting_kv_dict[ucid]['lang_on_ip'] = False
                        new_player.lang_on_ip = ucid_setting_kv_dict[ucid]['lang_on_ip']

                else:  # new user, add preference? set default?
                    # print("new user: " + ucid)
                    # if new user then add en_default?
                    # or check ip address?
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
                    # try:
                    #     url = "http://ipinfo.io/" + ipaddr.split(':')[0] + "/json?token=6ced84669ab3df"
                    #     # url = "http://api.hostip.info/get_json.php?ip=" + ipaddr.split(':')[0]
                    #     r = requests.get(url)
                    #     ip_dt = r.json()
                    #
                    #     # ip: "27.18.37.67"
                    #     # city: "Wuhan"
                    #     # region: "Hubei"
                    #     # country: "CN"
                    #     # loc: "30.5801,114.2730"
                    #
                    #     country_code = ip_dt['country']
                    #     print("new user country code:", country_code)
                    #     if country_code == 'CN':
                    #         init_lang = 'cn'
                    #     elif country_code == 'US':
                    #         init_lang = 'en'
                    #     else:  # other country code
                    #         init_lang = "en"
                    # except requests.exceptions.ConnectionError:
                    #     print(f"Fail to acquire IP data. Assign EN as default language for "
                    #           f"user {player_name} ({ucid}) at {ipaddr}")
                    # except urllib3.exceptions.ProtocolError:
                    #     print(f"Fail to acquire IP data. Assign EN as default language for "
                    #           f"user {player_name} ({ucid}) at {ipaddr}")
                    # except http.client.RemoteDisconnected:
                    #     print(f"Fail to acquire IP data. Assign EN as default language for "
                    #           f"user {player_name} ({ucid}) at {ipaddr}")

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
                cdi.player_net_config_by_name[player_name] = new_player
                # print(new_player.__dict__)  # DCS: new_player dict
            f_obj.seek(0)
            json.dump(ucid_setting_kv_dict, f_obj)
            f_obj.truncate()
