import plugins.declare_plugins
from .weapon_delivery_evaluation import declare, plugin_name
# from plugins.range_control.obsolete.weapon_tracker import declare_weapon_tracker_event_handler

plugins.declare_plugins.plugin_mains[plugin_name] = declare
# declare()
# print("test declared")
