# -*- coding: utf-8 -*-

from unimonapi import UnimonError

HOST, HOST_GROUP, TEMPLATE, USER, USER_GROUP, SCRIPT, TRIGGER, DISCO_RULE = range(8)

API_OBJECT_KEYS = {
    HOST:        { 'name': 'host',          'visible_name': 'name',         'id': 'hostid',     'ids': 'hostids' },
    HOST_GROUP:  { 'name': 'name',          'visible_name': 'name',         'id': 'groupid',    'ids': 'groupids' },
    TEMPLATE:    { 'name': 'host',          'visible_name': 'name',         'id': 'templateid', 'ids': 'templateids' },
    USER:        { 'name': 'alias',         'visible_name': 'name',         'id': 'userid',     'ids': 'userids' },
    USER_GROUP:  { 'name': 'name',          'visible_name': 'name',         'id': 'usrgrpid',   'ids': 'usrgrpids' },
    SCRIPT:      { 'name': 'name',          'visible_name': 'name',         'id': 'scriptid',   'ids': 'scriptids' },
    TRIGGER:     { 'name': 'description',   'visible_name': 'description',  'id': 'triggerid',  'ids': 'triggerids' },
    DISCO_RULE:  { 'name': 'name',          'visible_name': 'name',         'id': 'druleid',    'ids': 'druleids' },
}

def get_object_type_by_id_key(id_key):
    for object_type in API_OBJECT_KEYS:
        if API_OBJECT_KEYS[object_type]['id'] == id_key:
            return object_type
    return UnimonError('Unsupported Zabbix API object ID key: ' + id_key)

def get_api_method_by_type(zabbix_api, object_type):
    if object_type == HOST:          return zabbix_api.host.get
    elif object_type == HOST_GROUP:  return zabbix_api.hostgroup.get
    elif object_type == TEMPLATE:    return zabbix_api.template.get
    elif object_type == USER:        return zabbix_api.user.get
    elif object_type == USER_GROUP:  return zabbix_api.usergroup.get
    elif object_type == SCRIPT:      return zabbix_api.script.get
    elif object_type == TRIGGER:     return zabbix_api.trigger.get
    elif object_type == DISCO_RULE:  return zabbix_api.drule.get
    else:
        raise UnimonError('Unsupported Zabbix API object type: ' + object_type)

def get_object_name(zabbix_api, id, object_type, visible=False):
    api_metod = get_api_method_by_type(zabbix_api, object_type)
    ids_key = API_OBJECT_KEYS[object_type]['ids']
    if visible:
        name_key = API_OBJECT_KEYS[object_type]['visible_name']
    else:
        name_key = API_OBJECT_KEYS[object_type]['name']
    kwargs = {
        ids_key:  [id],
        'output': [name_key],
    }
    objects = api_metod(**kwargs)
    if len(objects) == 0: return None
    return objects[0][name_key]

def get_object_id(zabbix_api, name, object_type, visible=False):
    api_metod = get_api_method_by_type(zabbix_api, object_type)
    id_key = API_OBJECT_KEYS[object_type]['id']
    if visible:
        name_key = API_OBJECT_KEYS[object_type]['visible_name']
    else:
        name_key = API_OBJECT_KEYS[object_type]['name']
    objects = api_metod(filter={name_key: name}, output=[id_key])
    if len(objects) == 0: return None
    return objects[0][id_key]

def lookup_object(zabbix_api, object, object_type, by_id=True, visible=False):
    if by_id:
        return get_object_name(zabbix_api, object, object_type, visible)
    else:
        return get_object_id(zabbix_api, object, object_type, visible)

def prepare_object_for_import_export(zabbix_api, object, object_key=None, export=True, filter_keys=[], expand_keys=[], copy_keys={}, rename_keys={}, custom_keys={}):
    ''' Prepare raw Zabbix API object for export or exported object for import by:
        - filtering read-only parameters,
        - expanding IDs to names (and vice versa),
        - copying and renaming needed parameters,
        - custom processing.
    '''

    if isinstance(object, dict):
        for key in object.keys():
            if key in copy_keys:
                to_key = copy_keys[key]
                if to_key in object:
                    object[to_key] = object[key]

            if key in rename_keys:
                to_key = rename_keys[key]
                object[to_key] = object[key]
                del object[key]

            if key in custom_keys:
                custom_prepare_function = custom_keys[key]
                object[key] = custom_prepare_function(zabbix_api, object[key], export)

        for key in object.keys():
            if key in filter_keys:
                del object[key]
            else:
                object[key] = prepare_object_for_import_export(zabbix_api, object[key],
                    export=export,
                    object_key=key,
                    filter_keys=filter_keys,
                    expand_keys=expand_keys,
                    copy_keys=copy_keys,
                    rename_keys=rename_keys,
                    custom_keys=custom_keys,
                )

    elif isinstance(object, list):
        for i in range(len(object)):
            object[i] = prepare_object_for_import_export(zabbix_api, object[i],
                export=export,
                object_key=object_key,
                filter_keys=filter_keys,
                expand_keys=expand_keys,
                copy_keys=copy_keys,
                rename_keys=rename_keys,
                custom_keys=custom_keys,
            )

    elif object_key in expand_keys:
        if object != '0':
            object_type = get_object_type_by_id_key(object_key)
            expanded_object = lookup_object(zabbix_api, object, object_type, by_id=export)
            if expanded_object is not None:
                object = expanded_object
            else:
                raise UnimonError(u'Object "{}" not found: {}'.format(object_key, object))

    return object
