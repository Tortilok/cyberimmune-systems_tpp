def check_operation(id, details):
    authorized = False
    src = details.get('source')
    dst = details.get('deliver_to')
    opr = details.get('operation')

    if not all((src, dst, opr)):
        return False

    print(f"[info] checking policies for event {id},  {src}->{dst}: {opr}")

    if src == 'scada-receiver' and dst == 'task-scheduler' and \
            opr in ('check_sensors', 'update_settings', \
                    'turbine_stop', 'turbine_start'):
        authorized = True
    elif src == 'task-scheduler' and dst == 'authorization-verifier':
        authorized = True
    elif src == 'task-scheduler' and dst == 'command-block' and \
            opr in ('send_message', 'turbine_stop', 'turbine_start'):
        authorized = True
    elif src == 'authorization-verifier' and dst == 'task-scheduler' and \
            (opr == 'send_message'):
        authorized = True
    elif src == 'authorization-verifier' and dst == 'license-verifier':
        authorized = True
    elif src == 'license-verifier' and dst == 'task-scheduler':
        authorized = True
    elif src == 'command-block' and dst == 'scada-sender' and \
            opr == 'send_message':
        authorized = True
    elif src == 'scada-sender' and dst == 'scada' and opr == 'send_message':
        authorized = True
    elif src == 'data-processor-analog' and dst == 'data-storage' and \
            opr == 'store_analog':
        authorized = True
    elif src == 'data-processor-discrete' and dst == 'data-storage' and \
            opr == 'store_discrete':
        authorized = True
    elif src == 'data-processor-analog' and dst == 'app' and \
            opr == 'store_analog':
        authorized = True
    elif src == 'data-processor-discrete' and dst == 'app' and \
            opr == 'store_discrete':
        authorized = True
    elif src == 'command-block' and dst == 'app' and opr == 'check_sensors':
        authorized = True
    elif src == 'app' and dst == 'data-verifier' and opr == 'verify':
        authorized = True
    elif src == 'task-scheduler' and dst == 'command-block' and \
            opr == 'check_sensors':
        authorized = True
    elif src == 'data-verifier' and dst == 'app' and opr in \
            ('get_data',):
        authorized = True
    elif src == 'data-verifier' and dst == 'data-storage' and opr in \
            ('get_data',):
        authorized = True
    elif src == 'app' and dst == 'data-verifier' and \
                opr in ('verify_data'):
        authorized = True
    elif src == 'data-storage' and dst == 'data-verifier' and \
                opr in ('verify_data'):
        authorized = True
    elif src == 'data-verifier' and dst == 'command-block' and \
            opr == 'send_message':
        authorized = True
    elif src == 'app-receiver' and dst == 'update-manager' and \
            opr == 'update_app':
        authorized = True
    elif src == 'update-manager' and dst == 'task-scheduler' and \
            opr == 'update_app':
        authorized = True
    elif src == 'task-scheduler' and dst == 'update-manager' and \
            opr == 'verify_app':
        authorized = True
    elif src == 'update-manager' and dst == 'app-verifier' and \
            opr == 'check_license':
        authorized = True
    elif src == 'app-verifier' and dst == 'app-storage' and \
            opr == 'get_file_content':
        authorized = True
    elif src == 'app-storage' and dst == 'app-verifier' and \
            opr == 'get_file_content':
        authorized = True
    elif src == 'license-verifier' and dst == 'task-scheduler' and \
            opr == 'update_app':
        authorized = True
    elif src == 'task-scheduler' and dst == 'app-updater' and \
            opr == 'update_settings':
        authorized = True
    elif src == 'app-updater' and dst == 'app' and \
            opr == 'update_settings':
        authorized = True
    elif src == 'task-scheduler' and dst == 'update-manager' and \
            opr == 'update_settings':
        authorized = True
    elif src == 'update-manager' and dst == 'app-updater' and \
            opr == 'update_settings':
        authorized = True
    elif src == 'app' and dst == 'command-block' and \
            opr == 'send_message':
        authorized = True

    # kea - Kafka events analyzer - an extra service for internal monitoring,
    # can only communicate with itself
    if src == 'kea' and dst == 'kea' \
            and (opr == 'self_test' or opr == 'test_param'):
        authorized = True  
    
    return authorized