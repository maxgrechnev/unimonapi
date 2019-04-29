# -*- coding: utf-8 -*-

from unimonapi import UnimonError
import lookup
import logging

FILTER_KEYS = [
    'actionid',
    'operationid',
    'opcommand_grpid',
    'opcommand_hstid',
    'opconditionid',
    'conditionid',
    'eval_formula',
]

EXPAND_KEYS = [
    'groupid',
    'hostid',
    'usrgrpid',
    'userid',
    'templateid',
    'scriptid',
]

COPY_KEYS = {
    'eval_formula': 'formula',
}

RENAME_KEYS = {
    'recoveryOperations': 'recovery_operations',
    'acknowledgeOperations': 'acknowledge_operations',
}

def expand_filter_condition_values(zabbix_api, conditions, export=True):
    for condition in conditions:
        # TODO: Expand discovery check and proxy IDs
        if condition['conditiontype'] == '0':       object_type = lookup.HOST_GROUP
        elif condition['conditiontype'] == '1':     object_type = lookup.HOST
        elif condition['conditiontype'] == '2':     object_type = lookup.TRIGGER
        elif condition['conditiontype'] == '13':    object_type = lookup.TEMPLATE
        elif condition['conditiontype'] == '18':    object_type = lookup.DISCO_RULE
        else:                                       object_type = None

        if object_type is not None:
            value = lookup.lookup_object(zabbix_api, condition['value'], object_type, by_id=export)
            if value:
                condition['value'] = value
            else:
                raise UnimonError(u'Object of type {} not found: {}'.format(unicode(object_type), condition['value']))

    return conditions

def filter_actions_maintenance_mode(zabbix_api, actions, export=True):
    # Filter maintenance_mode for not trigger actions
    for action in actions:
        if action['eventsource'] != '0':
            if 'maintenance_mode' in action:
                del action['maintenance_mode']
            elif 'pause_suppressed' in action:
                del action['pause_suppressed']
    return actions

def export_actions(zabbix_api):
    actions = zabbix_api.action.get(
        output='extend', selectFilter='extend',
        selectOperations='extend',
        selectRecoveryOperations='extend',
        selectAcknowledgeOperations='extend',
    )
    return lookup.prepare_object_for_import_export(zabbix_api, {'actions': actions},
        export=True,
        filter_keys=FILTER_KEYS,
        expand_keys=EXPAND_KEYS,
        copy_keys=COPY_KEYS,
        rename_keys=RENAME_KEYS,
        custom_keys={
            'conditions': expand_filter_condition_values,
            'actions': filter_actions_maintenance_mode,
        }
    )['actions']

def import_actions(zabbix_api, actions_to_import, overwrite=True, delete=False):
    log = logging.getLogger()
    existing_actions_list = zabbix_api.action.get(output='extend')
    existing_actions_dict = { action['name']: action for action in existing_actions_list }
    kwargs = {
        'export': False,
        'expand_keys': EXPAND_KEYS,
        'custom_keys': {
            'conditions': expand_filter_condition_values,
        },
    }

    for action in actions_to_import:
        name = action['name']
        if name in existing_actions_dict:
            if overwrite:
                id = existing_actions_dict[name]['actionid']
                log.info('Update action "{}"'.format(name.encode('utf-8')))
                # Filter eventsource: cannot update this parameter
                action = lookup.prepare_object_for_import_export(zabbix_api, action, filter_keys=['eventsource'], **kwargs)
                zabbix_api.action.update(actionid=id, **action)
                log.info('Action updated')
        else:
            log.info('Create action "{}"'.format(name.encode('utf-8')))
            action = lookup.prepare_object_for_import_export(zabbix_api, action, **kwargs)
            zabbix_api.action.create(**action)
            log.info('Action created')

    if delete:
        action_names_to_import = [ action['name'] for action in actions_to_import ]
        actions_to_delete = {
            action['actionid']: action['name']
                for action in existing_actions_list
                    if action['name'] not in action_names_to_import
        }
        if len(actions_to_delete) > 0:
            log.info('Delete actions: ' + unicode(actions_to_delete.values()).encode('utf-8'))
            zabbix_api.action.delete(*actions_to_delete.keys())
            log.info('Actions deleted')
