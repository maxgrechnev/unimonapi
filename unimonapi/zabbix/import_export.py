# -*- coding: utf-8 -*-

from macros import export_macros
from macros import import_macros
from discovery_rules import export_discovery_rules
from discovery_rules import import_discovery_rules
from actions import export_actions
from actions import import_actions
import logging, json

EXPORT_KEYS = [
    'templates',
    'triggers',
    'value_maps',
    'hosts',
    'graphs',
    'version',
    'groups',
]

def export_configs(zabbix_api, auto_created=False):
    template_ids = zabbix_api.template.get(output=['templateid'], preservekeys=True).keys()
    host_ids = zabbix_api.host.get(output=['hostid'], preservekeys=True).keys()
    value_map_ids = zabbix_api.valuemap.get(output=['valuemapid'], preservekeys=True).keys()
    host_group_ids = zabbix_api.hostgroup.get(output=['groupid'], preservekeys=True).keys()
    export_result = zabbix_api.configuration.export(
        format='json',
        options={
            'templates': template_ids,
            'hosts': host_ids,
            'valueMaps': value_map_ids,
            'groups': host_group_ids,
        }
    )
    export_result = json.loads(export_result)
    export_result = export_result['zabbix_export']
    export_result = {
        key: export_result[key]
            for key in EXPORT_KEYS
                if key in export_result
    }
    export_result['macros'] = export_macros(zabbix_api)
    export_result['discovery_rules'] = export_discovery_rules(zabbix_api)
    export_result['actions'] = export_actions(zabbix_api)
    return export_result

def import_rule(create=None, update=None, delete=None):
    import_rule = {}
    if create is not None: import_rule['createMissing'] = create
    if update is not None: import_rule['updateExisting'] = update
    if delete is not None: import_rule['deleteMissing'] = delete
    return import_rule

def delete_missing_hosts(zabbix_api, hosts_to_import):
    log = logging.getLogger()
    host_names_to_import = [ host['host'] for host in hosts_to_import ]
    existing_hosts = zabbix_api.host.get(output=['host', 'hostid'])
    hosts_to_delete = {
        host['hostid']: host['host']
            for host in existing_hosts
                if host['host'] not in host_names_to_import
    }
    if len(hosts_to_delete) > 0:
        log.info('Delete hosts: ' + unicode(hosts_to_delete.values()).encode('utf-8'))
        zabbix_api.host.delete(*hosts_to_delete.keys())
        log.info('Hosts deleted')

def delete_missing_templates(zabbix_api, templates_to_import):
    log = logging.getLogger()
    template_names_to_import = [ template['template'] for template in templates_to_import ]
    existing_templates = zabbix_api.template.get(output=['host', 'templateid'])
    templates_to_delete = {
        template['templateid']: template['host']
            for template in existing_templates
                if template['host'] not in template_names_to_import
    }
    if len(templates_to_delete) > 0:
        log.info('Delete templates: ' + unicode(templates_to_delete.values()).encode('utf-8'))
        zabbix_api.template.delete(*templates_to_delete.keys())
        log.info('Templates deleted')

def delete_missing_value_maps(zabbix_api, value_maps_to_import):
    log = logging.getLogger()
    value_map_names_to_import = [ value_map['name'] for value_map in value_maps_to_import ]
    existing_value_maps = zabbix_api.valuemap.get(output=['valuemapid', 'name'])
    value_maps_to_delete = {
        value_map['valuemapid']: value_map['name']
            for value_map in existing_value_maps
                if value_map['name'] not in value_map_names_to_import
    }
    if len(value_maps_to_delete) > 0:
        log.info('Delete value maps: ' + unicode(value_maps_to_delete.values()).encode('utf-8'))
        zabbix_api.valuemap.delete(*value_maps_to_delete.keys())
        log.info('Value maps deleted')

def delete_missing_host_groups(zabbix_api, groups_to_import):
    log = logging.getLogger()
    group_names_to_import = [ group['name'] for group in groups_to_import ]
    existing_groups = zabbix_api.hostgroup.get(output=['name', 'internal', 'groupid'])
    groups_to_delete = {
        group['groupid']: group['name']
            for group in existing_groups
                if (
                    group['name'] not in group_names_to_import and
                    group['internal'] != '1'
                )
    }
    if len(groups_to_delete) > 0:
        log.info('Delete host groups: ' + unicode(groups_to_delete.values()).encode('utf-8'))
        zabbix_api.hostgroup.delete(*groups_to_delete.keys())
        log.info('Host groups deleted')

def import_configs(zabbix_api, config, overwrite=True, delete=False):
    log = logging.getLogger()
    if 'macros' in config:
        import_macros(zabbix_api, config['macros'], overwrite, delete)
    if 'discovery_rules' in config:
        import_discovery_rules(zabbix_api, config['discovery_rules'], overwrite, delete)

    if delete:
        # Zabbix API method "configuration.import" cannot delete these objects:
        if 'hosts' in config:
            delete_missing_hosts(zabbix_api, config['hosts'])
        if 'templates' in config:
            delete_missing_templates(zabbix_api, config['templates'])
        if 'value_maps' in config:
            delete_missing_value_maps(zabbix_api, config['value_maps'])
        if 'groups' in config:
            delete_missing_host_groups(zabbix_api, config['groups'])

    import_source = {
        key: config[key]
            for key in EXPORT_KEYS
                if key in config
    }
    import_source = { 'zabbix_export': import_source }
    log.info('Import objects: ' + str(EXPORT_KEYS))
    zabbix_api.confimport(
        confformat='json',
        source=json.dumps(import_source),
        rules={
            'applications':     import_rule(create=True, delete=delete),
            'discoveryRules':   import_rule(create=True, update=overwrite, delete=delete),
            'graphs':           import_rule(create=True, update=overwrite, delete=delete),
            'groups':           import_rule(create=True),
            'hosts':            import_rule(create=True, update=overwrite),
            'httptests':        import_rule(create=True, update=overwrite, delete=delete),
            'items':            import_rule(create=True, update=overwrite, delete=delete),
            'templateLinkage':  import_rule(create=True),
            'templates':        import_rule(create=True, update=overwrite),
            'templateScreens':  import_rule(create=True, update=overwrite, delete=delete),
            'triggers':         import_rule(create=True, update=overwrite, delete=delete),
            'valueMaps':        import_rule(create=True, update=overwrite),
        },
    )
    log.info('Objects imported')
    if 'actions' in config:
        import_actions(zabbix_api, config['actions'], overwrite, delete)
