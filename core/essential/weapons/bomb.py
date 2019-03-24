"""
This file implements data model for general purpose bomb and guided bomb
what about sub-munition you ask?
"""
import collections
from .weapon import Weapon


class Bomb(Weapon):
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        super().__init__(weapon_runtime_id, weapon_data, timestamp)

    # what differs bomb from other types of ammunition?
    # bomb can be rippled or paired
