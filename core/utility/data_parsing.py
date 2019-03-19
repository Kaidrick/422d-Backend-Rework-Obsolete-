import numpy as np
import core.utility.utils as utils
import time


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def record_position_time_pair(pos, pos_list: list, pos_time_list: list):
    if len(pos_list) > 9:  # only keep 10 pieces of data
        pos_list.pop(0)
        pos_time_list.pop(0)

    # after removing obsolete data
    pos_list.append(pos)
    pos_time_list.append(time.time())

    return pos_list, pos_time_list


def calc_velocity(data: list, time_stamp: list):
    last_dt = data[-1]
    s_idx = -1

    while True:
        try:
            s_idx -= 1
            if not data[s_idx - 1] == last_dt:  # different data, break
                break
        except IndexError:  # chances are there are not enough data to calculate speed
            return None  # not enough data

    p1 = utils.pos_to_np_array(last_dt)
    p0 = utils.pos_to_np_array(data[s_idx])

    t1 = time_stamp[-1]
    t0 = time_stamp[s_idx]

    p_vel = (p1 - p0) / (t1 - t0)  # vector
    return p_vel


def position_change_over_time_difference(data: list, time_stamp: list):
    last_dt = data[-1]
    s_idx = -1

    while True:
        try:
            s_idx -= 1
            if not data[s_idx - 1] == last_dt:  # different data, break
                break
        except IndexError:  # chances are there are not enough data to calculate speed
            return None  # not enough data

    p1 = utils.pos_to_np_array(last_dt)
    p0 = utils.pos_to_np_array(data[s_idx])

    t1 = time_stamp[-1]
    t0 = time_stamp[s_idx]

    try:
        # print(p0, p1)
        v = np.linalg.norm(p1 - p0) / (t1 - t0)  # in meters per second
    except ZeroDivisionError:  # somehow the time difference is zero
        v = 0
    return v
#
# if __name__ == '__main__':
#     test_data = [
#         {'x': 235356, 'y': -2343, 'z': 4253246},
#         # {'x': 235356, 'y': -2343, 'z': 4253246},
#         # {'x': 223436, 'y': -2343, 'z': 756775},
#         # {'x': 34657, 'y': -5413, 'z': 945},
#         # {'x': 572, 'y': -7546, 'z': 567},
#         # {'x': 64258, 'y': -2343, 'z': 7560383},
#         # {'x': 8575, 'y': -3567, 'z': 929274},
#     ]
#     test_time = [
#         75675461,
#         # 75675462,
#         # 75675463,
#         # 75675464,
#         # 75675465,
#         # 75675466,
#         # 75675467
#     ]
#     print(change_over_time_difference(test_data, test_time))

if __name__ == '__main__':
    test_data = [
                {'x': 235356, 'y': -2343, 'z': 425326},
                {'x': 984532, 'y': -5413, 'z': 756775},
                {'x': 223436, 'y': -2343, 'z': 756775},
                {'x': 34657, 'y': -5413, 'z': 945},
                {'x': 572, 'y': -7546, 'z': 567},
                {'x': 64258, 'y': -2343, 'z': 7560383},
                {'x': 8575, 'y': -3567, 'z': 929274},
    ]
    test_pos_record = []
    test_pos_time_record = []
    for i in range(1, 21):
        record_position_time_pair(test_data[i], test_pos_record, test_pos_time_record)
    print(test_pos_record, test_pos_time_record)
