import plugins.declare_plugins
from plugins.airport_atis.airport_atis import plugin_name, include_airport_atis

plugins.declare_plugins.plugin_mains[plugin_name] = include_airport_atis
