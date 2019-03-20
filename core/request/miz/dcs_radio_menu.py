from core.request.miz.dcs_action import DcsAction, ActionType
from core.request.miz.dcs_env import airbase_dict, env_player_dict, set_msg_locale, \
    search_localized_string, dcs_message_format as mf
from core.request.miz import dcs_env as db
from administrative import MOTD, RULES, FAQ

from core.request.miz.dcs_weather import RequestDcsWeather, parse_wx
from core.request.miz.dcs_message import RequestDcsMessageForGroup
from core.request.miz.dcs_navigation import find_nearest_airbase, get_2d_xy_dist, get_dir_vector, vec2hdg, generate_ll_deg_min, \
    generate_mgrs_std
from core.request.api.player_preference import find_ucid_by_group_id, find_player_preferences_by_group_id, set_player_preference_lang, \
    set_player_preference_unit
from core.request.api.api_debug import RequestAPINetDostring
import numpy as np
import gettext
import core.data_interface as cdi
import core.request.miz.dcs_event
import time
import core.spark as spark
from core.request.miz.dcs_event import EventHandler
from core.request.miz.dcs_debug import RequestDcsDebugCommand

# only interact with player through radio, so this is the only file that should contain a _(...) function?
_ = gettext.gettext


map_name = {
    'PersianGulf': _("Persian Gulf Proving Ground hosted by 422d TES."),
    'Nevada': _("Nevada Test and Training Range hosted by 422d TES."),
    'Caucasus': _("Black Sea Free Roaming Map hosted by 422d TEST.")
}


class RadioPull:  # paths
    def __init__(self):
        self.NavLink_self_pos = [_("Nav Link"), _("My Position")]
        self.NavLink_near_airbase = [_("Nav Link"), _("Nearest Airport")]

        self.Weather_self_wx = [_('Wx Link'), _('Atmosphere Data At My Position')]
        self.Weather_datis_near_ab = [_('Wx Link'), _('D-ATIS From the Nearest Airport')]

        self.Utility_tankers_on_sta = [_('Utils Link'), _('Tankers on Station')]

        self.Preference_set_english = [_("Preferences"), _("Language Settings"), _("Set English as default language")]
        self.Preference_set_chinese = [_("Preferences"), _("Language Settings"), _("Set Chinese as default language")]
        self.Preference_set_japanese = [_("Preferences"), _("Language Settings"), _("Set Japanese as default language")]

        self.Preference_set_metric_unit = [_("Preferences"), _("System of Measurement"), _("Metric, always use")]
        self.Preference_set_imperial_unit = [_("Preferences"), _("System of Measurement"), _("Imperial, always use")]
        self.Preference_set_mixed_unit = [_("Preferences"), _("System of Measurement"), _("Either, usage depends on aircraft type")]
        self.Preference_set_all_unit = [_("Preferences"), _("System of Measurement"), _("Metric Plus Imperial, always show me data in both")]

        self.ServInfo_admin_motd = [_("Server Information"), _("Administrative"), _("View Message Of The Day")]
        self.ServInfo_admin_rules = [_("Server Information"), _("Administrative"), _("Rules")]
        self.ServInfo_admin_faq = [_("Server Information"), _("Administrative"), _("FAQ")]


class RadioItem:
    def __init__(self, text, group_id, remove_upon_exec=None, parent_path=None, click_action="click", attach=-1):
        # init as RadioItem("Click me!", some_unit, a_click_action_obj, path="some path")
        self.group_id = group_id  # whose radio menu has this item?
        self.parent_path = parent_path  # path, parent must be a radio menu
        self.click_action = click_action  # if no action, then submenu?
        self.remove_upon_exec = remove_upon_exec  # None if radio menu
        self.text = str(text)  # text for this radio item?
        self.path = None
        self.attach = attach
        self.path_find()

        if type(attach) is list:
            attach.append(self)

    def ap(self, lta):
        lta[:] += [self]

    def path_find(self):  # generate path of this radio item?
        if self.parent_path is None:  # add to radio menu root (F.10 Other)
            # print("parent_path is None!")
            self.path = [self.text]

        else:  # parent_path is not None, then
            self.path = self.parent_path + [self.text]


# how to design the click_action part?
class RadioClickAction:
    def __init__(self, r_add, r_remove):
        self.add = r_add  # radio item list to be added
        self.remove = r_remove  # radio item list to be removed
        self.pull_request = "weather?"  # so this is a pull from server
        # the pull may pull something like, weather?
        self.text = ""


class AddRadioItem(DcsAction):  # this is a request
    def __init__(self, radio_item_list):  # radio_item is a RadioItem object
        # so lua should know these attributes
        super().__init__(ActionType.ADD_RADIO)
        self.content = []
        for radio_item in radio_item_list:
            p_l = {
                'group_id': radio_item.group_id,
                'parent_path': radio_item.parent_path,
                'click_action': radio_item.click_action,
                'remove_upon_exec': radio_item.remove_upon_exec,
                'text': radio_item.text,
                'path': radio_item.path,
            }
            self.content.append(p_l)


class RemoveRadioItem(DcsAction):  # this is a request
    def __init__(self, radio_item_list, mode='specific'):  # radio_item is a RadioItem object
        # so lua should know these attributes
        super().__init__(ActionType.RM_RADIO)
        self.content = []
        self.mode = mode  # specific(remove every entry) or all(remove whole menu)

        for radio_item in radio_item_list:
            p_l = {
                'group_id': radio_item.group_id,
                'path': radio_item.path,
            }
            self.content.append(p_l)


class SanitizeRadioItem(DcsAction):
    def __init__(self, group_id, mode='specific'):  # radio_item is a RadioItem object
        # so lua should know these attributes
        super().__init__(ActionType.SANITIZE_RADIO)
        self.group_id = group_id
        self.mode = mode  # specific(remove every entry) or all(remove whole menu)


def init_radio_menu_for_group(group_id, player_name):  # TODO: Add more radio items
    go = []

    ref_player = cdi.active_players[player_name]

    # pref = find_player_preferences_by_group_id(group_id)
    # group_lang = pref['lang']
    # group_lang = cdi.active_players_by_group_id[group_id].language
    group_lang = ref_player.language
    # group_lang = 'en'
    # print("set language to: " + group_lang)
    global _
    _ = set_msg_locale(group_lang, 'dcs_radio_menu')

    # check if the group_id key exists in the env_group_dict
    # if group_id in cdi.active_players_by_group_id.keys():
    #     print(f"Init radio menu for {group_id}")

    # group_player_name = db.env_group_dict[group_id].lead['player_name']
    # ipaddr = env_player_dict[group_player_name].ipaddr
    # ucid = env_player_dict[group_player_name].ucid

    # group_player_name = cdi.active_players_by_group_id[group_id].player_name
    group_player_name = ref_player.player_name
    # ipaddr = cdi.active_players_by_group_id[group_id].ipaddr
    ipaddr = ref_player.ipaddr
    # ucid = cdi.active_players_by_group_id[group_id].ucid
    ucid = ref_player.ucid

    # lang_on_ip = cdi.active_players_by_group_id[group_id].lang_on_ip
    lang_on_ip = ref_player.lang_on_ip

    if lang_on_ip:
        lang_on_ip_message = _("Based on your DCS World client language setting, "
                               "422d TES server has automatically set English "
                               "as your default display language."
                               "\nYou can always set your "
                               "preference via in-game radio menu option <F.10 Other>")
        RequestDcsMessageForGroup(group_id, lang_on_ip_message).send()

    # initialization message for player
    player_init_msg = group_player_name + _(", welcome to ") + _(map_name[cdi.theatre]) + "\n" + \
        _("Here is your connection info:") + "\n" + \
        _("IP Address: ") + f"{ipaddr}" + "\n" + \
        _("UCID: ") + f"{ucid}" + "\n" + \
        "\n" + \
        _("Check Radio Menu <F.10 Other> for more information and options.")

    RequestDcsMessageForGroup(group_id, player_init_msg).send()

    # Server Information Board TODO: Modulize radio items and menu? If module then? import module radio item control?
    # tree: Server Information
    svr_info = RadioItem(_("Server Information"), group_id, None, None, attach=go)
    # tree: Server Information -> Administrative
    admin = RadioItem(_("Administrative"), group_id, None, svr_info.path, attach=go)
    # tree: Server Information -> Administrative -> View Message Of The Day
    motd = RadioItem(_("View Message Of The Day"), group_id, False, admin.path, attach=go)
    # tree: Server Information -> Administrative -> Rules
    rules = RadioItem(_("Rules"), group_id, False, admin.path, attach=go)
    # tree: Server Information -> Administrative -> FAQ
    faq = RadioItem(_("FAQ"), group_id, False, admin.path, attach=go)

    # Battle Link
    btlk = RadioItem(_("Battle Link"), group_id, None, svr_info.path, attach=go)  # only works if mission available?

    wx = RadioItem(_("Wx Link"), group_id, None, None, attach=go)
    wx_owner = RadioItem(_("Atmosphere Data At My Position"), group_id, False, wx.path, attach=go)
    wx_near_datis = RadioItem(_("D-ATIS From the Nearest Airport"), group_id, False, wx.path, attach=go)

    # Navigation Link
    navlk = RadioItem(_("Nav Link"), group_id, None, None, attach=go)
    near_ab = RadioItem(_("Nearest Airport"), group_id, False, navlk.path, attach=go)

    # Utility Link
    utlk = RadioItem(_("Utils Link"), group_id, None, None, attach=go)
    trk_info = RadioItem(_("Tankers on Station"), group_id, False, utlk.path, attach=go)

    # User Preferences
    settings = RadioItem(_("Preferences"), group_id, None, None, attach=go)
    translation_setting = RadioItem(_("Translation Settings"), group_id, None, settings.path, attach=go)
    translate_unit = RadioItem(_("Translate Unit of Measurement"), group_id, None, translation_setting.path, attach=go)
    translate_unit_yes = RadioItem(_("Enable"), group_id, True, translate_unit.path, attach=go)
    translate_unit_no = RadioItem(_("Disable"), group_id, True, translate_unit.path, attach=go)

    lang_setting = RadioItem(_("Language Settings"), group_id, None, settings.path, attach=go)
    lang_set_en = RadioItem(_("Set English as default language"), group_id, False, lang_setting.path, attach=go)
    lang_set_cn = RadioItem(_("Set Chinese as default language"), group_id, False, lang_setting.path, attach=go)
    lang_set_jp = RadioItem(_("Set Japanese as default language"), group_id, False, lang_setting.path, attach=go)

    system_of_measurement_setting = RadioItem(_("System of Measurement"), group_id, None, settings.path, attach=go)
    som_set_imperial = RadioItem(_("Imperial, always use"), group_id, False, system_of_measurement_setting.path, attach=go)
    som_set_metric = RadioItem(_("Metric, always use"), group_id, False, system_of_measurement_setting.path, attach=go)
    som_set_mixed = RadioItem(_("Either, usage depends on aircraft type"), group_id, False, system_of_measurement_setting.path, attach=go)
    som_set_all = RadioItem(_("Metric Plus Imperial, always show me data in both"), group_id, False, system_of_measurement_setting.path, attach=go)

    # add plugin_functions radios here

    k = AddRadioItem(go)
    k.send()

    db.env_group_radio_dict[group_id] = go
    # print(env_group_radio_dict)


def response_to_radio_item_pull(pull):  # TODO: add system of measurement preferences
    # get pull group info
    group_id = pull['group_id']
    if group_id not in cdi.active_players_by_group_id.keys():  # no such group active in game
        print(f"group id {group_id} not active in mission env")
        return

    # pos = {}
    # # check group name
    # group_name = db.env_group_dict[group_id].name
    # for export_id, unit_data in cdi.unit_precise_positions.items():
    #     if unit_data['GroupName'] == group_name:  # this group exists
    #         pos = unit_data['Position']
    #         break

    # find the location, search group dictionary

    # group_dict = db.env_group_dict[group_id]
    # player_name = group_dict.lead['player_name']

    player_dt = cdi.active_players_by_group_id[group_id]
    player_name = player_dt.player_name

    ucid = player_dt.ucid

    # what type of aircraft is the player flying? avoid ground unit
    # type_name = group_dict.lead['type']  # only apply mixed units if type_name is an aircraft / helicopter type name
    type_name = player_dt.unit_type

    mixed_system_of_measurement_dict = {
        'AV8BNA': 'imperial',
    }

    pos = player_dt.unit_pos
    # ll_coord = group_dict.lead['coord']['LL']
    ll_coord = [player_dt.unit_ll['Lat'], player_dt.unit_ll['Long'], player_dt.unit_ll['Alt']]
    # mgrs = group_dict.lead['coord']['MGRS']
    mgrs_str = "<MGRS string placeholder>"  # generate_mgrs_std(mgrs)

    lang = env_player_dict[player_name].language  # current language

    # what unit does the player want?
    unit = env_player_dict[player_name].preferred_system

    if unit == 'mixed':
        if type_name in mixed_system_of_measurement_dict.keys():
            unit = mixed_system_of_measurement_dict[type_name]
        else:  # not defined unit type, always use imperial then
            unit = 'imperial'

    # print("Preference settings: ", lang, unit)

    global _
    _ = set_msg_locale(lang, 'dcs_radio_menu')  # what is the current locale? find in player dict--> indexed by player name
    _RadioPull = RadioPull()

    # DCS: Radio path responses
    if pull['path'] == _RadioPull.Weather_self_wx:
        wx = RequestDcsWeather([pos]).send()
        parsed_wx = parse_wx(wx[0])
        lla = generate_ll_deg_min(ll_coord[0], ll_coord[1], ll_coord[2], 'metric')

        feet = ll_coord[2] * 3.28084
        # only convert unit if necessary
        # consider imperial units as the default preference
        p = parsed_wx
        n = ll_coord
        k = lla

        if p['wind'] == 0:  # no wind?
            wind_string = _("Wind: ") + _("Calm")
        else:
            if unit == 'imperial':
                wind_string = _("Wind: ") + f"{p['wind_kt']:.0f}" + _("kts") + "\n" + \
                          _("Wind Direction: ") + f"{p['mag_wind_dir']:05.1f}"
            elif unit == 'metric':
                wind_string = _("Wind: ") + f"{p['wind']:.0f}" + _("m/s") + "\n" + \
                              _("Wind Direction: ") + f"{p['mag_wind_dir']:05.1f}"
            elif unit == 'all':
                wind_string = _("Wind: ") + f"{p['wind']:.0f}" + _("m/s") + " " + _("or") + " " + f"{p['wind_kt']:.0f}" + _("kts") + "\n" + \
                              _("Wind Direction: ") + f"{p['mag_wind_dir']:05.1f}"

        # check user preferred unit:
        if unit == 'imperial':
            message = _("Weather at your Location: ") + f"{k[0]} {k[1]}" + " " + _("at") + " " + f"{feet:.0f}" + _("ft") + "\n" + \
                      f"{mgrs_str}" + "\n" + \
                      wind_string + "\n" + \
                      _("OAT: ") + f"{p['oat_fahrenheit']:.1f}" + _("°F") + "\n" + \
                      _("QNH: ") + f"{p['out_pres_inhg']:.2f}" + _("inHg")

        elif unit == 'metric':  # metric
            message = _("Weather at your Location: ") + f"{k[0]} {k[1]}" + " " + _("at") + " " + f"{k[2]}" + _("m") + "\n" + \
                      f"{mgrs_str}" + "\n" + \
                      wind_string + "\n" + \
                      _("OAT: ") + f"{p['oat_celsius']:.1f}" + _("°C") + "\n" + \
                      _("QNH: ") + f"{p['out_pres']:.0f}" + _("hP")

        elif unit == 'all':  # display both
            message = _("Weather at your Location: ") + f"{k[0]} {k[1]}" + " " + _("at") + " " + f"{k[2]}" + _("m") + " " + _("or") + " " + f"{feet:.0f}" + _("ft") + "\n" + \
                      f"{mgrs_str}" + "\n" + \
                      wind_string + "\n" + \
                      _("OAT: ") + f"{p['oat_celsius']:.1f}" + _("°C") + " " + _("or") + " " + f"{p['oat_fahrenheit']:.1f}" + _("°F") + "\n" + \
                      _("Pressure: ") + f"{p['out_pres']:.2f}" + _("hP") + " " + _("or") + " " + f"{p['out_pres_inhg']:.2f}" + _("inHg")

        RequestDcsMessageForGroup(group_id, message.lstrip('\n')).send()

    # DCS: path of difference radio items and corresponding radio message
    elif pull['path'] == _RadioPull.NavLink_near_airbase:  # Response: Nearest Airbase near me

        # find the location, search group dictionary
        # group_dict = db.env_group_dict[group_id]
        # pos = group_dict.lead_pos

        wx = RequestDcsWeather([pos]).send()
        parsed_wx = parse_wx(wx[0])
        ncorr = parsed_wx['ncorr']

        airbase_name = find_nearest_airbase(pos)
        dist = get_2d_xy_dist(pos, airbase_dict[airbase_name].pos)  # in meters?

        hdg_vec3 = get_dir_vector(pos, airbase_dict[airbase_name].pos)
        t_hdg = vec2hdg(hdg_vec3, mode='rad')
        f_hdg = np.rad2deg(t_hdg + ncorr)

        _airbase_name = search_localized_string(airbase_name, lang, 'dcs_airbases')

        if unit == 'imperial':
            # convert to nautical miles
            dist_nm = dist / 1852
            message = _("Nearest airport is ") + _airbase_name + _(". Fly heading ") + \
                f"{f_hdg:05.1f}" + _(" for ") + f"{dist_nm:.1f}" + _("nm")
        elif unit == 'metric':
            # convert to meters
            dist_km = dist / 1000
            message = _("Nearest airport is ") + _airbase_name + _(". Fly heading ") + \
                f"{f_hdg:05.1f}" + _(" for ") + f"{dist_km:.1f}" + _("km")
        elif unit == 'all':
            # show the player both
            dist_nm = dist / 1852
            dist_km = dist / 1000
            message = _("Nearest airport is ") + _airbase_name + _(". Fly heading ") + \
                f"{f_hdg:05.1f}" + _(" for ") + f"{dist_nm:.1f}" + _("nm") + " " + _("or") + " " + f"{dist_km:.1f}" + _("km")

        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Weather_datis_near_ab:
        airbase_name = find_nearest_airbase(pos)
        _airbase_name = search_localized_string(airbase_name, lang, 'dcs_airbases')

        # check if D-ATIS available
        if airbase_name in cdi.d_atis.keys():
            kn_datis = cdi.d_atis[airbase_name]
            info_letter = kn_datis['info_ident']
            time_string = kn_datis['time_string']
            mag_wind_dir = kn_datis['mag_wind_dir']
            wind_kt = kn_datis['wind_kt']
            wind_mps = kn_datis['wind_mps']
            oat = kn_datis['oat']
            altimeter = kn_datis['altimeter']
            altimeter_hp = kn_datis['altimeter_hp']
            rw_in_use = kn_datis['rw_in_use']

            # TODO: add wind calm if wind speed is less than 1 knot

            message = _("D-ATIS Uplink from ") + _airbase_name + "\n" + \
                _("Info ") + info_letter + " " + time_string + "Z" + "\n" + \
                _("Wind ") + f"{mag_wind_dir:.1f}" + _(" at ") + f"{wind_kt:.1f}" + _(" kts") + _(" or ") + \
                f"{wind_mps:.1f}" + _(" mps") + "\n" + _("Temperature ") + f"{oat:.0f}" + "\n" + \
                _("Altimeter ") + f"{altimeter:.2f}" + _(" or ") + f"{altimeter_hp:.0f}" + "\n" + \
                _("Runway ") + f"{rw_in_use}" + _(" in use") + "\n" + _("Information ") + info_letter + _(" End")

        else:  # not available
            message = _("D-ATIS download failed. No available D-ATIS from nearest station.")

        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Utility_tankers_on_sta:
        tanker_on_sta_string = _("Tanker Unit(s) on Station: ") + "\n"
        if len(cdi.tanker_sta.items()) > 0:
            for tanker_name, tanker_data in cdi.tanker_sta.items():
                track = tanker_data['track']
                ac_type = tanker_data['type']
                on_track_spd = tanker_data['on_track_spd']
                track_alt = tanker_data['alt']
                chn = tanker_data['chn']
                mode = tanker_data['mode']
                ident = tanker_data['ident']
                freq = tanker_data['freq']  # in Hz?
                callsign = tanker_data['callsign']

                kn_data_str = _("Track ") + track + " " + f"{on_track_spd:.0f}" + _(" at Angel ") + \
                    f"{(float(track_alt) / 1000):.0f}" + "\n" + \
                    ac_type + "<callsign_ph>" + f"{ident} {chn}{mode}" + \
                    " COMM " + f"{(freq / 1000000):.2f}MHz" + "\n"

                tanker_on_sta_string += kn_data_str

            message = tanker_on_sta_string
        else:
            message = _("No tanker on station at the moment.")

        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Preference_set_chinese:  # Response: Change preferred display language to CN
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_lang(ucid, 'cn')
        player_dt.language = 'cn'

        try:
            cdi.active_players_by_group_id[group_id].lang_on_ip = False
        except Exception as e:
            print(e)
            print("Error caught, continue")

        SanitizeRadioItem(group_id).send()  # remove all radio items
        init_radio_menu_for_group(group_id)  # repopulate radio items?

    elif pull['path'] == _RadioPull.Preference_set_english:  # Response: Change preferred display language to EN
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_lang(ucid, 'en')
        player_dt.language = 'en'

        try:
            cdi.active_players_by_group_id[group_id].lang_on_ip = False
        except Exception as e:
            print(e)
            print("Error caught, continue")

        SanitizeRadioItem(group_id).send()  # remove all radio items, use sanitize instead?
        init_radio_menu_for_group(group_id)  # repopulate radio items?

    elif pull['path'] == _RadioPull.Preference_set_japanese:  # Response: Change preferred display language to JP
        set_player_preference_lang(ucid, 'jp')
        player_dt.language = 'jp'

        try:
            cdi.active_players_by_group_id[group_id].lang_on_ip = False
        except Exception as e:
            print(e)
            print("Error caught, continue")

        SanitizeRadioItem(group_id).send()  # remove all radio items, use sanitize instead?
        init_radio_menu_for_group(group_id)  # repopulate radio items?

    elif pull['path'] == _RadioPull.Preference_set_imperial_unit:  # Response: Change preferred display unit to imperial
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_unit(ucid, 'imperial')
        player_dt.preferred_system = 'imperial'
        message = _("You have set Imperial Units as your preferred system of measurement.")
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Preference_set_metric_unit:  # Response: Change preferred display unit to metric
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_unit(ucid, 'metric')
        player_dt.preferred_system = 'metric'
        message = _("You have set Metric System as your preferred system of measurement.")
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Preference_set_mixed_unit:  # Response: Change preferred display unit to mixed
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_unit(ucid, 'mixed')
        player_dt.preferred_system = 'mixed'
        message = _("You have set Mixed Units as your preferred system of measurement.")
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.Preference_set_all_unit:  # Response: Change preferred display unit to all units
        # ucid = find_ucid_by_group_id(group_id)
        set_player_preference_unit(ucid, 'all')
        player_dt.preferred_system = 'all'
        message = _("You have set to display data in both Imperial and Metric System of measurement.")
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.ServInfo_admin_rules:  # Response: User reads Server Rules
        _ = set_msg_locale(lang, 'administrative')
        message = mf(_(RULES))
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.ServInfo_admin_faq:  # Response: User reads Server FAQ
        _ = set_msg_locale(lang, 'administrative')
        message = mf(_(FAQ))
        RequestDcsMessageForGroup(group_id, message).send()

    elif pull['path'] == _RadioPull.ServInfo_admin_motd:  # Response: User reads Server MOTD
        _ = set_msg_locale(lang, 'administrative')
        message = mf(_(MOTD))
        RequestDcsMessageForGroup(group_id, message).send()


def init_radio_menu_on_birth_spark(spark_dt):
    # print(spark_dt)
    player_group_id = spark_dt['data']['group_id']
    player_name = spark_dt['data']['name']
    player_runtime_id = spark_dt['data']['runtime_id']
    # print(player_group_id, player_name, player_runtime_id)

    SanitizeRadioItem(player_group_id).send()  # remove all existing radio items from this group
    # init_radio_menu_for_group(player_group_id)
    RequestDcsMessageForGroup(player_group_id, "Welcome! We are doing some major overhaul! Lots of functions"
                                               " are currently missing from the server. Use this mission "
                                               "as a free fly practice.").send()


spark.SparkHandler.PLAYER_SPAWN["dcs_radio_init_on_birth"] = init_radio_menu_on_birth_spark
