"""
This file implement methods that parse and analyze the pulled chat command from player.
Initially player should be able to use chat command to search for some unit data
the second step is to add a package function (like groups or raid in an rpg game)
add some function to the package to make it meaningful
unit conversion with chat command
simple math calculation
administrative functions with chat command
administrative debug functions with chat command
"""
import random
from core.request.api.api_net_message import RequestNetMessage
from core.request.api.api_debug import RequestApiLoadString
from core.request.miz.dcs_message import RequestDcsMessageForGroup
import core.utility.system_of_measurement_conversion as conv
import core.data_interface as cdi
import gettext
from core.request.miz.dcs_env import set_msg_locale, env_player_dict
from core.request.miz.dcs_player import RequestPlayerInfo

_ = gettext.gettext


def repeat_msg(msg):
    print(msg)


# Help info format
# <syntax name>:
#     <usage code> or <usage code>
#
#     <description>
# """
syntax_error = _("Syntax Error: ")
unit_conversion_error = _("Unit Conversion Error: ")
database_error = _("Database Search Error: ")
coord_conversion_error = _("Coordinates Conversion Error: ")

syntax_catalog = {  # format: <do><something>, <target_conv_type><stm><to stm>
    # system core
    'info': {
        'vkw': ['info', '信息', 'xinxi', 'chaxun', '查询'],
        'fmt': _("info <search_item> <specific_data> <other_args>"),
        'demo': ["info scud range", "info c-130 mtow", "info nellis afb"],
        'detail': _("This function searches 422d Database for the given argument name"),
        'error': database_error,
    },
    # information query related
    'roll': {
        'vkw': ['roll'],
        'fmt': _("roll <range>"),
        'demo': ["roll 100", "roll 6"],
        'detail': _("Roll a dice to see in you are lucky! "
                    "This function rolls a n-face dice and show the number in chat window. "
                    "The result is a integer number from 1 to n. \n"
                    "Default roll range is from 1 to 100. "
                    "n can not be less than 2 and n must be an integer."),
        'error': syntax_error,
    },  # roll dice

    'help': {
        'vkw': ['help', '帮助', 'cmd', 'commands', 'cmds'],  # help message
        'fmt': _("help, help <syntax>"),
        'demo': ["help", "help info"],
        'detail': _("\nAll available chat commands are as follows: "),
        'notation': _("\nUse \"help <syntax>\" command to display help info for this specific syntax usage."),
        'error': syntax_error,
    },

    # coordinates conversion
    'll': {
        'vkw': ['ll', 'latlon', '经纬'],
        'fmt': _("ll <UTM Zone><MGRS Digraph><Easting><Northing>, white space can be used to separate"),
        'demo': ["ll 11S QA 13524 21578"],
        'detail': _("Convert a coordinate from MGRS format to L/L format. "
                    "You can add white space to separate UTM Zone(grid zone designator, GZD), "
                    "MGRS Digraph(100,000-meter square identifier) and numerical location.\n"
                    "Please be aware that the converted L/L coordinate is in degrees and minutes, "
                    "not degrees, minites and seconds.\n"
                    "The format of ddmm.mmm provides more accuracy and is the standard format "
                    "used in most of aircrafts' navigation system in DCS World.\n"
                    "You should enter full coordinates as the parameters. "
                    "That means, parameters must contain UTM Zone and MGRS Digraph. "
                    "In case of missing UTM Zone and MGRS Digraph, if you are in an aircraft, "
                    "your aircraft's UTM Zone and MGRS Digraph will be used for this command; "
                    "otherwise this command will raise an error and send detailed error message back to you."),
        'error': coord_conversion_error,
        # no unit for coord conversion
        # """
        # An example of an MGRS coordinate, or grid reference, would be 4QFJ12345678, which consists of three parts:
        #
        # 4Q (grid zone designator, GZD)
        # FJ (the 100,000-meter square identifier)
        # 12345678 (numerical location; easting is 1234 and northing is 5678, in this case specifying a location with 10 m resolution)
        # """
    },

    'mgrs': {
        'vkw': ['mgrs', 'utm', '战术', '战术坐标'],
        'fmt': _("mgrs <Latitude> <Longitude> <Altitude>, "
                 "mgrs <Latitude Degree> <Latitude Minutes> <Longitude Degree> <Longitude Minutes> <Altitude>, "
                 "while <Altitude> is optional"),
        'demo': ["mgrs 36 24.124 -114 53.42"],
        'detail': _("Convert a coordinates from L/L format to MGRS format. "
                     "Please be aware how a L/L coordinates is written, you can use either: \n"
                     "1. Latitude and Longitude in degrees and minutes, not in degrees minutes seconds only. "
                     "For example: \n"
                     "\t36°14.473' North, 114°32.052' West is written as 36 14.473 -114 32.052\n"
                     "Notice the negative sign before the longitude is used to represent \"west\", "
                     "but there is no need to add \"+\" before latitude or longitude to indicate North or East.\n"
                     "2. Latitude and Longitude in degrees only. For example: \n"
                     "\t36°14.473' North, 114°32.052' West is written as 36.24122 -114.53420 \n\n"
                     "Finally, if you really want to, you can add N, W, E, or S to indicates North West East South, "
                     "either before the number or after the number. You can use white space to separate each elements, "
                     "such as: \n"
                     "\tN36 14.473 E114 32.052\n"      # args length is 4
                     "\t36 14.473N 114 32.052E\n"      # args length is 4
                     "\tN 36 14.473 E 114 32.052\n"    # args length is 6
                     "\t36 14.473 N 114 32.052 E\n"),  # args length is 6
        'error': coord_conversion_error,
    },
    
    
    # unit conversion
    'meter': {
        'vkw': ['meter', 'meters', '米', 'm'],
        'method': conv.feet2meters,
        'fmt': _("meter <number in feet>, meter [list of numbers in feet]"),
        'demo': ["meter 10000", "meter 20 50 100 200 500 1000"],
        'detail': _("Convert a number (or a series of number) from imperial feet to metric meters.\n"
                    "If the list of number has more than 5 numbers to be converted, "
                    "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("ft"),
        'p_unit': _("m"),
    },

    'feet': {
        'vkw': ['ft', 'feet', 'foot', '英尺'],
        'method': conv.meters2feet,
        'fmt': _("feet <number in meters>, feet [list of numbers in feet]"),
        'demo': ["feet 500", "feet 100 200 300 400 500"],
        'detail': _("Convert a number (or a series of number) from metric meters to imperial feet.\n"
                    "If the list of number has more than 5 numbers to be converted, "
                    "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("m"),
        'p_unit': _("ft"),
    },

    'mile': {
        'vkw': ['nm', 'mile', 'miles', '海里'],
        'method': conv.km2nm,
        'fmt': _("nm <number in kilometers>, nm [list of numbers in kilometers]"),
        'demo': ["nm 20", "nm 1 5 10 15 30"],
        'detail': _("Convert a number (or a series of number) from metric kilometers to nautical miles.\n"
                    "If the list of number has more than 5 numbers to be converted, "
                    "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("km"),
        'p_unit': _("nm"),
    },

    'kilometer': {
        'vkw': ['km', 'kilometer', 'kilometers', '千米'],
        'method': conv.nm2km,
        'fmt': _("km <number in nautical miles>, km [list of numbers in nautical miles]"),
        'demo': ["nm 20", "nm 1 5 10 15 30"],
        'detail': _("Convert a number (or a series of number) from nautical miles to metric kilometers.\n"
                    "If the list of number has more than 5 numbers to be converted, "
                    "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("nm"),
        'p_unit': _("km"),
    },

    'knot': {
        'vkw': ['kt', 'kts', 'knot', 'knots', '节'],
        'method': conv.kmh2kts,
        'fmt': _("kts <number in kilometers per hour>, kts [list of numbers in kilometers per hour]"),
        'demo': ['kt 20', 'knot 30', 'kts 40', 'knots 70 80 90 100'],
        'detail': _("Convert a number (or a series of number) in kilmeters per hour to knots.\n"
                  "If the list of number has more than 5 numbers to be converted, "
                  "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("km/h"),
        'p_unit': _("kts"),
    },

    'kmh': {
        'vkw': ['kmh', 'kmph', '千米时', '千米/时'],
        'method': conv.kts2kmh,
        'fmt': _("kmh <number in knots>, kmh [list of numbers in knots]"),
        'demo': ['kt 20', 'knot 30', 'kts 40', 'knots 70 80 90 100'],
        'detail': _("Convert a number (or a series of number) in kilometers per hour to knots.\n"
                   "If the list of number has more than 5 numbers to be converted, "
                   "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("kts"),
        'p_unit': _("km/h"),
    },

    'kg': {
        'vkw': ['kg', 'kgs', 'kilogram', 'kilograms', '千克', '公斤'],
        'method': conv.lbs2kg,
        'fmt': _("kg <number in pounds>, kg [list of numbers in pounds]"),
        'demo': ['kg 2000', 'kgs 150', 'kilogram 150', 'kilograms 150'],
        'detail': _("Convert a number (or a series of numbers) in pounds to metric kilograms.\n"
                    "If the list of number has more than 5 numbers to be converted, "
                    "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("lbs"),
        'p_unit': _("kg")
    },

    'lbs': {
        'vkw': ['lb', 'lbs', 'pound', 'pounds', '磅', '英镑'],
        'method': conv.kg2lbs,
        'fmt': _("lbs <number in kilograms>, lbs [list of numbers in kilograms]"),
        'demo': ['lb 2000', 'lbs 150', 'pound 150', 'pounds 150'],
        'detail': _("Convert a number (or a series of numbers) in kilograms to pounds.\n"
                   "If the list of number has more than 5 numbers to be converted, "
                   "you must be in a unit to receive the response message by trigger text due to message length."),
        'error': unit_conversion_error,
        'e_unit': _("kg"),
        'p_unit': _("lbs")
    },



    # # coord conversion
    # 'll': ['ll', 'latlon', '经纬'],  # coord conversion related
    # 'dir': ['bra', 'dir'],
    # 'bullseye': ['bullseye', 'bulls'],
    # 'mgrs': ['mgrs', 'grid', 'utm'],
    # 'vec3': ['xy', 'vec3'],  # convert to LO coord. end users shouldn't really care about this one
    # # group and package functions
    # 'group': ['g', 'group', 'p', 'party', 'package'],
    # # administrative functions
    # 'admin': ['admin', 'administrator', '管理'],  # admin options
    # # debug functions
    # 'debug': ['debug', '调试'],  # debug options
}


syntax_demo = {
    # system core
    'info': "info <search_item> - search data in 422d Database",  # information query related
    'roll': "roll <range> - roll a n-face dice",  # roll dice
    'help': "help - show all available chat commands",  # help message
    # unit conversion
    'meter': "meter <number in feet> - convert imperial feet to metric meters. Usage: ",
    'foot': "ft <number in meters>",
    'knot': "kt <meters per second>",
    'mile': "nm <number in km>",  # ofc it's nautical miles, are you fucking stupid or what?
    'kilometer': "km <number in nautical miles>",
    # coord conversion
    'll': "ll <bearing> <range> <alt> or ll <mgrs string>",  # coord conversion related
    'dir': "dir <Lat> <Lon>",
    'bullseye': "bulls <Lat> <Lon>",
    'mgrs': "mgrs <Lat> <Lon>",
    'vec3': "xy <x><y><z>",  # convert to LO coord. end users shouldn't really care about this one
    # group and package functions
    'group': "g join",
    # administrative functions
    'admin': "admin kick",  # admin options
    # debug functions
    'debug': "",  # debug options
}

# chat message keyword might be in many forms


# TODO: what is player is not in a unit
# check if player of this playerID is in a unit
# check if this unit exist in game
# do it by first check NetPlayerInfoById[PlayerID].slotID, if slotID is not '' then
# net.get_player_info() -> slot -> if slot not '' then ->

# if kw is a search function then call for search engine
# if kw is a conversion function then do conversion
# if kw is a group function then call for group methods and objects


def value_conversion(catalog_key, args):
    force_ingame_msg = False
    if args:  # convert to meter
        raw_conv = syntax_catalog[catalog_key]['method'](args)
        if type(raw_conv) is not None:
            if type(raw_conv) is not list:
                res = f"{args}" + _(syntax_catalog[catalog_key]['e_unit']) + \
                      _(" equals to ") + f"{raw_conv:.2f} " + _(syntax_catalog[catalog_key]['p_unit'])

            else:  # is a list
                res = ""
                for idx, s_raw_conv in enumerate(raw_conv):
                    if s_raw_conv is not None:
                        res += f"{args[idx]}" + _(syntax_catalog[catalog_key]['e_unit']) + \
                               _(" equals to ") + \
                               f"{s_raw_conv:.2f}" + _(syntax_catalog[catalog_key]['p_unit']) + "\n"
                    else:  # a None item
                        res += _(syntax_catalog[catalog_key]['error']) + \
                               f"Invalid argument. Check your input: {args}\n"

                p_res = res.split('\n')
                if len(p_res) > 5:
                    force_ingame_msg = True
        else:  # conv returns None
            res = _(syntax_catalog[catalog_key]['error']) + \
                  f"Unsupported type. Check your input {args}\n"

    else:
        res = syntax_catalog[catalog_key]['error'] + "Expect at least one argument (got none)."

    return res, force_ingame_msg


def keyword_command(kw, msg, net_player_id):  # need to know player language before sending message
    try:
        kw = kw.lstrip("/")
        args = msg.split()[1:]
    except Exception as e:
        print(e, "probably because no arg is provided")
        args = []
    # do things according to the kw
    res = ""
    player_active = False
    force_ingame_msg = False
    force_chat_broadcast = False
    group_id = 0

    # check if player is in a unit, if not, depends on what kind of keyword it is, choose
    # to inform player to enter a unit in order to receive message or echo in chat
    p_info = RequestApiLoadString(f"return net.get_player_info({net_player_id})", echo_result=True).send()
    player_name = p_info['name']
    lang = env_player_dict[player_name].language

    global _
    _ = set_msg_locale(lang, 'chat_cmd_processor')  # should only be either cn or en

    # check if player is in a unit by accessing player data in cdi
    # if player_name not in cdi.active_players_by_name.keys():
    #     print(f"{player_name} not in an active unit. use chat echo")
    # else:
    #     player_active = True
    #     group_id =

    try:
        group_id = cdi.active_players_by_name[player_name].group_id
    except KeyError:  # player_name not accessible, player is not active
        print(f"{player_name} not in an active unit. use chat echo")
    else:
        player_active = True

    # if p_info['slot'] == '':  # player is in observer list
    #     print(f"{player_name} not in an active unit. use chat echo")
    # else:  # player occupies a slot but is not necessarily in an active unit
    #     # check if unit of this slot is in the active player list
    #
    #     for player_group_id, player_dt in cdi.active_players_by_group_id.items():
    #         if player_dt.player_name == player_name:
    #             group_id = player_group_id
    #             player_active = True
    #
    #             print(f"{player_name} in an active unit group id {group_id}. use trigger message")
    #             break  # break for loop, stop searching in cdi

    # if loop ended without player_active flag being set to True, then player is not active

    # DCS Chat Keyword: info
    if kw in syntax_catalog['info']['vkw']:  # asking for information search
        force_ingame_msg = True
        # if any args are provided they start from [1]
        try:
            info_tp = args[0]  # exception may occur here
            # if player is in a unit, let user choose if they want chat echo or in-game message?
            res = f"Search data for {info_tp}"

        except Exception as e:
            print(e)
            res = f"Error: Invalid arguments or syntax usage"

    # DCS Chat Keyword: Roll
    elif kw in syntax_catalog['roll']['vkw']:  # roll takes direct control of net message, not res
        roll_err = False
        if args:  # an argument is passed
            # check if args is a single number
            try:
                bound = float(args[0])
                rolled_number = random.randint(1, bound)
                # res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-{int(bound)})"

            except Exception as e:  # show roll help
                print(e)
                res = syntax_catalog['roll']['error']
                roll_err = True

        else:  # no args passed, use default roll 100
            rolled_number = random.randint(1, 100)
            # res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-100)"

        # after finalize res, send localized message to each connected player based on language.
        if not roll_err:
            all_connected_players = RequestPlayerInfo().send()
            if all_connected_players:
                broadcast_rcv = {}

                for ucid, player_info in all_connected_players.items():
                    kn_broadcast_player_name = player_info['name']  # current name for this player
                    kn_broadcast_player_ucid = player_info['ucid']
                    net_id = player_info['playerID']

                    # get this specific player's language
                    # not the one who send the command
                    player_lang = cdi.player_net_config_by_ucid[kn_broadcast_player_ucid].language
                    _ = set_msg_locale(player_lang, "chat_cmd_processor")

                    # print(f"broadcast message to {kn_broadcast_player_name} using {player_lang}")
                    broadcast_rcv[kn_broadcast_player_name] = player_lang

                    if args:  # range is 1-100
                        res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-{int(bound)})"
                        RequestNetMessage(net_id, res).send()
                    else:  # no args
                        res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-100)"
                        RequestNetMessage(net_id, res).send()

                log_msg = f"Broadcast Net Message sent to "
                log_msg += str(len(broadcast_rcv.keys())) + " player(s): "
                for b_name, b_lang in broadcast_rcv.items():
                    log_msg += f"{b_name}({b_lang}); "

                print(log_msg)

            # for net_player_name, player_dt in cdi.player_net_config_by_name.items():
            #     player_lang = player_dt.language
            #     _ = set_msg_locale(player_lang, "chat_cmd_processor")
            #
            #     print(f"broadcast message to {net_player_name} using {player_lang}")
            #
            #     if args:  # range is 1-100
            #         res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-{int(bound)})"
            #         RequestNetMessage(player_dt.net_id, res).send()
            #     else:  # no args
            #         res = f"{player_name}" + _(" rolls ") + f"{rolled_number} (1-100)"
            #         RequestNetMessage(player_dt.net_id, res).send()

            return  # return after finish sending net message here
        # else let res be sent

    # DCS Chat Keyword: help
    elif kw in syntax_catalog['help']['vkw']:  # asking for list of available commands
        # check if an argument is passed
        catalog_info_msg = ""
        if args:  # an argument is passed, check if this is a valid syntax
            # check if length of arg is 1
            if len(args) == 1:  # else invalid
                for cata_k, cata_v in syntax_catalog.items():
                    if args[0] in cata_v['vkw']:  # belongs to this group of valid key word
                        catalog_info_msg += "Syntax - " + args[0] + "\n"
                        catalog_info_msg += "\t" + _(cata_v['fmt']) + "\n"
                        demo = cata_v['demo']
                        for s_demo in demo:
                            catalog_info_msg += "\t" + s_demo + "\n"
                        catalog_info_msg += "\n" + _(cata_v['detail']) + "\n"
            else:  # more than 1 args for some reason
                catalog_info_msg = _(syntax_catalog['help']['error']) + "Invalid Syntax."
        else:  # no args provided, return default help message
            fmt = _(syntax_catalog['help']['fmt'])
            demo = syntax_catalog['help']['demo']
            detail = _(syntax_catalog['help']['detail'])
            notation = _(syntax_catalog['help']['notation'])
            catalog_info_msg += _("Syntax - ") + kw + "\n"
            catalog_info_msg += "\n" + fmt + "\n"
            for s_demo in demo:
                catalog_info_msg += "\t" + s_demo + "\n"

            catalog_info_msg += "\t" + detail + "\n"
            for cata_k, cata_v in syntax_catalog.items():
                if 'fmt' in cata_v.keys():
                    catalog_info_msg += "\t" + _(cata_v['fmt']) + "\n"

            catalog_info_msg += notation

        res = catalog_info_msg

    # DCS Chat Keyword: meter
    elif kw in syntax_catalog['meter']['vkw']:  # convert feet to meters
        # supposedly the number in feet should be the
        # if args is provided then convert
        # if not provided, show error message and help info?
        catalog_key = 'meter'
        catalog_args = args
        res, force_ingame_msg = value_conversion(catalog_key, catalog_args)

        # DCS Chat Keyword: meter
    elif kw in syntax_catalog['feet']['vkw']:  # convert feet to meters
        # supposedly the number in feet should be the
        # if args is provided then convert
        # if not provided, show error message and help info?
        catalog_key = 'feet'
        catalog_args = args
        res, force_ingame_msg = value_conversion(catalog_key, catalog_args)

    elif kw in syntax_catalog['mile']['vkw']:
        res, force_ingame_msg = value_conversion('mile', args)

    elif kw in syntax_catalog['kilometer']['vkw']:
        res, force_ingame_msg = value_conversion('kilometer', args)

    elif kw in syntax_catalog['knot']['vkw']:
        res, force_ingame_msg = value_conversion('knot', args)

    elif kw in syntax_catalog['kmh']['vkw']:
        res, force_ingame_msg = value_conversion('kmh', args)

    elif kw in syntax_catalog['kg']['vkw']:
        res, force_ingame_msg = value_conversion('kg', args)

    elif kw in syntax_catalog['lbs']['vkw']:
        res, force_ingame_msg = value_conversion('lbs', args)


    # if player is not active and not by_net then send to net message
    # if player is active and not by_net
    # by_net override all other priority and ignore other option

    if force_ingame_msg:  # must be showed as in-game message, otherwise send notice rather than message.
        if player_active:  # active, can send by in-game message
            RequestDcsMessageForGroup(group_id, res).send()
        else:  # player not active, let the player know s/he must be in a unit in order to receive
            notice_res = "You must enter a unit before you can use this command due to response message length."
            RequestNetMessage(net_player_id, notice_res).send()
    else:  # force_ingame_msg
        if player_active:
            RequestDcsMessageForGroup(group_id, res).send()
        else:  # not active
            RequestNetMessage(net_player_id, res).send()


def process(cmd_pull):  # {'check_word': 'info', 'msg': 'info', 'type': 'chat_cmd'}
    msg = cmd_pull['msg']
    kw = cmd_pull['check_word']
    net_player_id = cmd_pull['player_id']

    keyword_command(kw, msg, net_player_id)

