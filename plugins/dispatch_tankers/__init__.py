import plugins.declare_plugins
from plugins.dispatch_tankers.tanker import plugin_name, include_dispatch_tankers

plugins.declare_plugins.plugin_mains[plugin_name] = include_dispatch_tankers
