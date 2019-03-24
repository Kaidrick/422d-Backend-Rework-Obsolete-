from .weapon import Weapon


class Rocket(Weapon):
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        super(Rocket, self).__init__(weapon_runtime_id, weapon_data, timestamp)
