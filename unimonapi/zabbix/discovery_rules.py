# -*- coding: utf-8 -*-

import logging
import lookup

def export_discovery_rules(zabbix_api):
    rules = zabbix_api.drule.get(output='extend', selectDChecks='extend')
    return lookup.prepare_object_for_import_export(zabbix_api, rules,
        export=True,
        filter_keys=[
            'druleid',
            'nextcheck',
            'dcheckid',
        ]
    )

def import_discovery_rules(zabbix_api, rules_to_import, overwrite=True, delete=False):
    log = logging.getLogger()
    existing_rules_list = zabbix_api.drule.get(output='extend')
    existing_rules_dict = { rule['name']: rule for rule in existing_rules_list }

    for rule in rules_to_import:
        name = rule['name']
        if name in existing_rules_dict:
            if overwrite:
                id = existing_rules_dict[name]['druleid']
                log.info('Update discovery rule "{}"'.format(name.encode('utf-8')))
                zabbix_api.drule.update(druleid=id, **rule)
                log.info('Discovery rule updated')
        else:
            log.info('Create discovery rule "{}"'.format(name.encode('utf-8')))
            zabbix_api.drule.create(**rule)
            log.info('Discovery rule created')

    if delete:
        rule_names_to_import = [ rule['name'] for rule in rules_to_import ]
        rules_to_delete = {
            rule['druleid']: rule['name']
                for rule in existing_rules_list
                    if rule['name'] not in rule_names_to_import
        }
        if len(rules_to_delete) > 0:
            log.info('Delete discovery rules: ' + unicode(rules_to_delete.values()).encode('utf-8'))
            zabbix_api.drule.delete(*rules_to_delete.keys())
            log.info('Discovery rules deleted')
