unit_of_measurement = {
    'AV8BNA': 'imperial',
    'FA-18C_hornet': 'imperial',
}


def get_aircraft_system(ac_type):
    try:
        return unit_of_measurement[ac_type]
    except KeyError:  # does not have data
        return 'imperial'
