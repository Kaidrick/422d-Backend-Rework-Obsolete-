# import configparser
import os
from plugins.declare_plugins import plugin_log
import core.data_interface as cdi
from core.request.miz.dcs_mark_panel import RequestAddMarkPanel, RequestRemoveMarkPanel, MarkPanel
import json
import gettext
from core.request.miz.dcs_env import set_msg_locale, search_localized_string
from core.request.miz.dcs_weather import parse_wx, RequestDcsWeather

_ = gettext.gettext

plugin_name = "Tactical Map Marker"

# TODO: the in-game panel no longer seems to support multiple lines of text diplay
# TODO: thus, the panel it self should probably only display basic information, while the chat command
# TODO: can be used to access detailed information?


plugin_log(plugin_name, f"Set Marker Data for '{cdi.theatre}'")

# player-panels dictionary
marker_panels_by_player_name = {}  # str: player_name, list: panels


def load_data():
    search_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', cdi.theatre)
    res = {}
    for filename in os.listdir(search_path):
        if filename.endswith('.json'):
            with open(os.path.join(search_path, filename)) as f:
                _dict = json.load(f)
                res[filename[:-5]] = _dict

    return res


tactical_markers_data = load_data()

"""
spk_dt = {
        'type': 'player_spawn',
        'data': {
            'name': kn_check.player_name,
            'group_id': kn_check.group_id,
            'unit_name': kn_check.unit_name,
            'runtime_id': kn_check.runtime_id
        }
    }
"""


def map_markers(spk_dt):  # this method should be added to signal handler list
    # sig_dt = {
    #     'initiator': unit_id_name,
    #     'type': "spawn",
    #     'player_name': player_name,
    #     'player_group_id': group_id,
    # }
    kn_markers = []  # temporary container var
    # in order to add marker, first need to know --> group_id
    group_id = spk_dt['data']['group_id']
    player_name = spk_dt['data']['name']
    player_lang = cdi.active_players_by_name[player_name].language

    _ = set_msg_locale(player_lang, "map_markers")

    # get position weather in one batch?
    for area, data in tactical_markers_data.items():
        for datum in data:
            name = search_localized_string(datum['name'], player_lang, "marker_data")
            data_type = datum['type']
            entry = search_localized_string(datum['entry'], player_lang, "marker_data")
            desc = search_localized_string(datum['desc'], player_lang, "marker_data")
            pos = datum['pos']
            if data_type == "info":  # information board for a land pack
                deco = _(" Information Board")
                text = name + deco + "\n" + \
                    "——————————————————————" + "\n" + \
                    desc + "\n\n" + \
                    _("Entry/Exit: ") + entry

            elif data_type == "area":  # information for a specific area or airspace, need wx
                deco = _(" Area")
                text = name + deco + "\n" + \
                    "——————————————————————" + "\n" + \
                    desc + "\n\n" + \
                    _("Ingress/Egress: ") + entry

            elif data_type == "dpi":  # desired point of impact, need wx
                h_d_p = []
                for angel in range(0, 31):
                    h_pos = pos.copy()
                    h_pos['y'] = angel * 1000 / 3.281

                    h_d_p.append(h_pos)

                # after mapping height to this position point
                new_wx = RequestDcsWeather(h_d_p).send()
                p_wx_string = ""

                land_qfe = None
                for angel, r_wx in enumerate(new_wx):
                    # if no wind then change line to 360 / 00, Temp N/A
                    p_wx = parse_wx(r_wx)
                    p_wx_string += f"{p_wx['mag_wind_dir']:03.0f} / {p_wx['wind_kt']:02.0f}, " \
                                   f"Temp {p_wx['oat_celsius']:.0f} @ ALT {angel + 1}\n"
                    land_qfe = f"{p_wx['qfe_hp']:.2f}"

                deco = _("Precision Target: ")
                text = deco + name + "\n" + \
                    "——————————————————————" + "\n" + \
                    desc + "\n\n" + \
                    _("Wx: ") + "\n" + \
                    _("QFE: ") + land_qfe + _(" hPa") + "\n" + \
                    p_wx_string

            elif data_type == "landmark":  # need deco, name and
                deco = _("Landmark: ")
                text = deco + name + "\n" + \
                    "——————————————————————" + "\n" + \
                    desc + "\n\n"

            else:
                text = name

            kn_mk = MarkPanel(group_id, text).set_pos(pos['x'], pos['z'])
            kn_markers.append(kn_mk)

    # cdi.active_players_by_name[player_name].marker_panels = kn_markers
    marker_panels_by_player_name[player_name] = kn_markers

    RequestAddMarkPanel(kn_markers).send()


# TODO: maybe make language and preference change as a signal as well?
def clean_markers(spk_dt):  # remove marker panel for player group when player leaves
    # group_id = spk_dt['group_id']
    player_name = spk_dt['data']['name']
    player_mark_panels = marker_panels_by_player_name[player_name]
    RequestRemoveMarkPanel(player_mark_panels).send()
    del marker_panels_by_player_name[player_name]  # remove entry on player de-spawn
