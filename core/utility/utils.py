"""Utility methods"""
import numpy as np


def pos_to_np_array(pos: dict):
    x = pos['x']
    y = pos['y']
    z = pos['z']
    kn_array = np.array([x, y, z])
    return kn_array


def bake_object_id(obj_id: int):
    return f"""{{['id_'] = {obj_id},}}"""


def bake_object_id_by_id_name(obj_id_name: str):
    b_obj_id = obj_id_name[3:]
    return f"""{{['id_'] = {b_obj_id},}}"""
