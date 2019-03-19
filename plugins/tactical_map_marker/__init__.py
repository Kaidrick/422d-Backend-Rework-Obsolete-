from plugin_functions.tactical_map_marker.map_markers import map_markers, clean_markers
import core.signal as sig

sig.SignalHandler.PLAYER_SPAWN["map_markers"] = map_markers
sig.SignalHandler.PLAYER_DESPAWN["clean_markers"] = clean_markers
