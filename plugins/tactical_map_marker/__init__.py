from plugins.tactical_map_marker.map_markers import map_markers, clean_markers
import core.spark as spark

spark.SparkHandler.PLAYER_SPAWN["map_markers"] = map_markers
spark.SparkHandler.PLAYER_DESPAWN["clean_markers"] = clean_markers
