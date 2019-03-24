import plugins.declare_plugins
from plugins.range_control.obsolete.player_tracker import plugin_name, run_player_tracker
from plugins.range_control.obsolete.shell_tracker import declare
from plugins.range_control.obsolete.weapon_tracker import declare_weapon_tracker_event_handler

plugins.declare_plugins.plugin_mains[plugin_name] = run_player_tracker
declare()
declare_weapon_tracker_event_handler()
