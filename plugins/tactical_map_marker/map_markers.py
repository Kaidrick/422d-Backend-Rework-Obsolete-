# import configparser
import os
from plugin_functions.declare_plugins import plugin_log
import core.data_interface as cdi
from core.request.miz.dcs_mark_panel import RequestAddMarkPanel, RequestRemoveMarkPanel, MarkPanel
import core.signal as sig
import json
import gettext
from core.request.miz.dcs_env import set_msg_locale, search_localized_string
from core.request.miz.dcs_weather import parse_wx, RequestDcsWeather

_ = gettext.gettext

plugin_name = "Tactical Map Marker"

# read markers config from the config file
# cfg = configparser.ConfigParser()

# get theatre
theatre = cdi.theatre

marker_files = {
    'Nevada': 'Nevada.json',
    # 'Caucasus': 'Caucasus.json',
    # 'PersianGulf': 'PersianGulf.json'
}

# cfg_file = marker_files[theatre]
cfg_file = 'Nevada.json'
#
# cfg.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), cfg_file))

plugin_log(plugin_name, f"Read Marker Data from file '{cfg_file}'")


def cdi_unit_data_search():
    pass


# TODO: for marker data, each json file is a small package of marker data for a specific location/area
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


def map_markers(signal_data):  # this method should be added to signal handler list
    # sig_dt = {
    #     'initiator': unit_id_name,
    #     'type': "spawn",
    #     'player_name': player_name,
    #     'player_group_id': group_id,
    # }
    kn_markers = []  # temporary container var
    # in order to add marker, first need to know --> group_id
    group_id = signal_data['player_group_id']
    player_lang = cdi.active_players_by_group_id[group_id].language

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

    cdi.active_players_by_group_id[group_id].marker_panels = kn_markers

    RequestAddMarkPanel(kn_markers).send()


# TODO: maybe make language and preference change as a signal as well?
def clean_markers(signal_data):  # remove marker panel for player group when player leaves
    group_id = signal_data['player_group_id']
    player_mark_panels = cdi.active_players_by_group_id[group_id].marker_panels

    RequestRemoveMarkPanel(player_mark_panels).send()
