from .range_missile_control import declare, plugin_name
from plugins.declare_plugins import plugin_mains

plugin_mains[plugin_name] = declare
