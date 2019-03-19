"""
This file implements methods that are used to convert between metric and imperial unit
"""
# convert string to float


def parse_numbers(number):
    try:
        return float(number)
    except ValueError as e:
        print("ValueError", e)
        return None


# scale conversion
def scale_convert(number, multiplier):
    """
    This method takes a number and multiply this number by given multiplier then return
    :param number:
    :param multiplier:
    :return:
    """
    if type(number) is str:  # meter 10000
        p_f = parse_numbers(number)
        if p_f:
            p_c = p_f * multiplier
            return p_c
        else:
            return None

    elif type(number) is float or type(number) is int:
        p_f = number
        p_c = p_f * multiplier
        return p_c

    elif type(number) is list:
        lr_res = []
        for p_f in number:  # for each item in feet list
            lr_res.append(scale_convert(p_f, multiplier))

        return lr_res
    else:  # not supported types, ignore
        print("debug info", "system_of_measurement_conversion.py", "def scale_convert", "unsupported types")
        return None


def meters2feet(meters):
    return scale_convert(meters, 3.28084)


def meters2nm(meters):
    return scale_convert(meters, 1 / 1852)


def meters2km(meters):
    return scale_convert(meters, 1 / 1000)


def feet2meters(feet):
    return scale_convert(feet, 0.3048)


def kts2kmh(kts):
    return scale_convert(kts, 0.514444)


def kmh2kts(mps):
    return scale_convert(mps, 1 / 1.852)


def nm2km(nm):
    return scale_convert(nm, 1.852)


def km2nm(km):
    return scale_convert(km, 0.539957)


def kg2lbs(kg):
    return scale_convert(kg, 2.20462)


def lbs2kg(lbs):
    return scale_convert(lbs, 0.453592)


def min2sec(d_min):
    return scale_convert(d_min, 60)


def sec2min(deg):
    return scale_convert(deg, 1 / 60)


if __name__ == '__main__':
    print(meters2feet(feet2meters(10000)))
    print(kts2kmh([1, 2, 3, 4, 5]))
    print(min2sec(.785))
    print(sec2min(32))

