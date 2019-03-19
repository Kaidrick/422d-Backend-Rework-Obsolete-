""" This file implements method to retrieve data from scripting engine in lua
 need to modify lua file to reduce the lua code in python string """
# TODO: write lua in lua! need refactoring!
import numpy as np
from core.request.miz.dcs_debug import RequestDcsDebugCommand


def get_north_correction(nc_x, nc_y, nc_z):
    # get north correction
    cmd = f"""return getNorthCorrection({{x = {nc_x}, y = {nc_y}, z = {nc_z}}})"""
    nc = RequestDcsDebugCommand(cmd, True).send()
    return nc


def get_pos_north_correction(pos: dict):
    nc_x = pos['x']
    nc_y = pos['y']
    nc_z = pos['z']
    return get_north_correction(nc_x, nc_y, nc_z)


def get_true_hdg_by_vector(vector: np.array):
    raw_hdg = np.arctan(vector[2] / vector[0])
    if vector[2] < 0:  # z is less than zero
        hdg = raw_hdg + np.pi
    else:
        hdg = raw_hdg

    return hdg


def get_mag_hdg_by_vector(vector: np.array, pos: dict, north_correction=None):
    raw_hdg = get_true_hdg_by_vector(vector)
    if north_correction:
        nc = north_correction
    else:
        nc = get_pos_north_correction(pos)

    mag_hdg = raw_hdg + nc
    if mag_hdg < 0:
        mag_hdg += np.pi

    return mag_hdg

