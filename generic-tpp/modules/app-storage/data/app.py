def process_data(sensors, settings):
    for sensor_setting in settings:
        for sensor in sensors:
            if sensor['name'] != sensor_setting['name']:
                continue
            if sensor['value'] < sensor_setting['min']:
                return True
            if sensor['value'] > sensor_setting['max']:
                return True
            
    return False