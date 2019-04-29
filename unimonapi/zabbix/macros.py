# -*- coding: utf-8 -*-

import logging
import lookup

def export_macros(zabbix_api):
    macros = zabbix_api.usermacro.get(globalmacro=True, output='extend')
    return lookup.prepare_object_for_import_export(zabbix_api, macros,
        export=True,
        filter_keys=['globalmacroid'],
    )

def import_macros(zabbix_api, macros_to_import, overwrite=True, delete=False):
    log = logging.getLogger()
    existing_macros_list = zabbix_api.usermacro.get(globalmacro=True, output='extend')
    existing_macros_dict = { macro['macro']: macro for macro in existing_macros_list }

    for macro in macros_to_import:
        name = macro['macro']
        value = macro['value']
        if name in existing_macros_dict:
            # Update only if value is different
            if overwrite and value != existing_macros_dict[name]['value']:
                id = existing_macros_dict[name]['globalmacroid']
                log.info('Update macro "{}"'.format(name.encode('utf-8')))
                zabbix_api.usermacro.updateglobal(globalmacroid=id, value=value)
                log.info('Macro updated')
        else:
            log.info('Create macro "{}"'.format(name.encode('utf-8')))
            zabbix_api.usermacro.createglobal(macro=name, value=value)
            log.info('Macro created')

    if delete:
        macros_names_to_import = [ macro['macro'] for macro in macros_to_import ]
        macros_to_delete = {
            macro['globalmacroid']: macro['macro']
                for macro in existing_macros_list
                    if macro['macro'] not in macros_names_to_import
        }
        if len(macros_to_delete) > 0:
            log.info('Delete macros: ' + unicode(macros_to_delete.values()).encode('utf-8'))
            zabbix_api.usermacro.deleteglobal(*macros_to_delete.keys())
            log.info('Macros deleted')
