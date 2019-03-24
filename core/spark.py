"""
This file implements spark functionality, which is the event like system in python backend
whenever a spark is sent by the backend, it should run the spark methods
"""


class SparkHandler:
    # player
    PLAYER_SPAWN = {}  # definitive signal of player spawn
    PLAYER_DESPAWN = {}  # definitive signal of player de-spawn
    CRASH = {}
    SHOT = {}
    SHOOTING_START = {}
    SHOOTING_END = {}
    ENGINE_STARTUP = {}  # doesn't really work for multi-player
    ENGINE_SHUTDOWN = {}  # doesn't really work for multi-player
    TAKEOFF = {}
    LAND = {}
    PLAYER_DISTANCE = {}  # player's position changes

    # weapon
    WEAPON_RELEASE = {}
    WEAPON_TERMINAL = {}

    # AI unit
    OTHER_SPAWN = {}
    OTHER_DESPAWN = {}

# """
# Signal data is a dictionary. It contains data similar to that of in-game event
# who did what on what time and other parameters
# {
#   initiator: player_name,
#   sig: signal_type,
#   params: other_params,
# }
#
# sig_dt = {
#     'initiator': runtime_id_name,
#     'type': "despawn",
#     'player_name': player_name,
#     'player_group_id': group_id,
# }
# """


def player_spawn(spark_dt):
    """
    This method is called when when a player spawn. It will then run all methods registered with spawn handler
    :param spark_dt: a dictionary {}
    :return:
    """
    for handler_id, handler_method in SparkHandler.PLAYER_SPAWN.items():
        handler_method(spark_dt)


def player_despawn(spark_dt):
    for handler_id, handler_method in SparkHandler.PLAYER_DESPAWN.items():
        handler_method(spark_dt)


def player_distance(spark_dt):
    for handler_id, handler_method in SparkHandler.PLAYER_DISTANCE.items():
        handler_method(spark_dt)


# -----------------------------------------------------------------------
def weapon_release(spark_dt):
    for handler_id, handler_method in SparkHandler.WEAPON_RELEASE.items():
        handler_method(spark_dt)


def weapon_terminal(spark_dt):
    for handler_id, handler_method in SparkHandler.WEAPON_TERMINAL.items():
        handler_method(spark_dt)


# -------------------------------------------------------------------------
# AI unit
def other_spawn(spark_dt):
    for handler_id, handler_method in SparkHandler.OTHER_SPAWN.items():
        handler_method(spark_dt)


def other_despawn(spark_dt):
    for handler_id, handler_method in SparkHandler.OTHER_DESPAWN.items():
        handler_method(spark_dt)
