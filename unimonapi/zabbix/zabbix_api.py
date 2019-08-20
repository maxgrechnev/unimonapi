# -*- coding: utf-8 -*-

from unimonapi import UnimonError
from unimonapi import WrongIpRange
from unimonapi import MonitoringAPI
from unimonapi import Event
from unimonapi import HostGroup
from import_export import export_configs
from import_export import import_configs
import lookup
from pyzabbix import ZabbixAPI as PyZabbixAPI
from pyzabbix import ZabbixAPIException
import logging, re, subprocess, threading

class ZabbixAPI(MonitoringAPI):

    MAX_DISCOVERY_ADDRESS_NUMBER = 64000
    DEFAULT_ZABBIX_PORT = 10050
    INSTALL_AGENT_TIMEOUT_SEC = 300
    NOT_CLASSIFIED, INFO, WARNING, AVERAGE, HIGH, DISASTER = range(6)

    SUPPORTED_AGENT_OS = [
        'Windows',
        'Linux',
    ]

    ZABBIX_TO_UNIMON_SEVERITY = {
        NOT_CLASSIFIED:    Event.INFO,
        INFO:            Event.INFO,
        WARNING:        Event.WARNING,
        AVERAGE:        Event.WARNING,
        HIGH:            Event.CRITICAL,
        DISASTER:        Event.CRITICAL,
    }

    def __init__(self, url, user, password, agent_repository=None, agent_install_win=None, agent_install_lin=None, match_filter='DUMMY'):
        self._agent_repository = agent_repository
        self._agent_install_win = agent_install_win
        self._agent_install_lin = agent_install_lin
        self._match_filter = match_filter
        self._zabbix_api = PyZabbixAPI(url)
        self._zabbix_api.login(user, password)
        self._log = logging.getLogger()
        self._log.info('Logged in to Zabbix API as ' + user)

    def get_max_discovery_address_number(self):
        return self.MAX_DISCOVERY_ADDRESS_NUMBER

    def _get_disco_rules(self):
        disco_rules = []
        disco_rules = self._zabbix_api.drule.get(output=['druleid', 'iprange'])

        if len(disco_rules) == 0:
            raise UnimonError('Discovery rules list is empty')

        return disco_rules

    def get_discovery_ip_range(self):
        disco_rules = self._get_disco_rules()
        return disco_rules[0]['iprange']

    def start_discovery(self, ip_range=None):
        disco_rules = self._get_disco_rules()
        try:
            for rule in disco_rules:
                if ip_range:
                    self._zabbix_api.drule.update(druleid = rule['druleid'], iprange = ip_range, status = 0)
                else:
                    self._zabbix_api.drule.update(druleid = rule['druleid'], status = 0)

        except ZabbixAPIException as e:
            if str(e).find('Incorrect value for field "iprange"') > -1:
                raise WrongIpRange('Incorrect IP range specified "{0}"'.format(ip_range), True)
            else:
                raise e

    def stop_discovery(self):
        disco_rules = self._get_disco_rules()
        for rule in disco_rules:
            self._zabbix_api.drule.update(druleid = rule['druleid'], status = 1)

    def _unimon_to_zabbix_severity(self, severities):
        zabbix_severities = []

        for severity in severities:
            for zabbix_severity in self.ZABBIX_TO_UNIMON_SEVERITY:
                if self.ZABBIX_TO_UNIMON_SEVERITY[zabbix_severity] == severity:
                    zabbix_severities.append(zabbix_severity)

        return zabbix_severities

    def _get_problems(self, zabbix_severities, groups=None):
        kwargs = {
            'output':        ['eventid', 'objectid'],
            'severities':    zabbix_severities,
            'selectTags':    ['tag', 'value'],
            'sortfield':    ['eventid'],
            'sortorder':    'DESC',
        }
        if groups:
            kwargs['groupids'] = groups

        return self._zabbix_api.problem.get(**kwargs)

    def _get_triggers_by_problems(self, problems):
        trigger_ids = []
        triggers = []

        for problem in problems:
            if problem['objectid'] not in trigger_ids:
                trigger_ids.append( problem['objectid'] )

        if len(trigger_ids) != 0:
            triggers = self._zabbix_api.trigger.get(
                output = ['triggerid', 'description', 'priority'],
                triggerids = trigger_ids,
                expandDescription = 1,
                selectHosts = ['name', 'hostid'],
                selectGroups = ['name', 'groupid'],
                preservekeys = True,
                monitored = 1,
                skipDependent = 1,
            )

        return triggers

    def _is_summary_trigger(self, trigger):
        for host_group in trigger['groups']:
            if not self._is_summary_group(host_group):
                return False

        return True

    def _is_summary_group(self, host_group):
        if host_group['name'].find(self._match_filter) != -1:
            return True
        else:
            return False

    def get_problems(self, severities=None, groups=None):
        if severities is None:
            severities = Event.SEVERITY_ICONS.keys()

        events = []
        zabbix_severities = self._unimon_to_zabbix_severity(severities)
        problems = self._get_problems(zabbix_severities, groups)
        triggers = self._get_triggers_by_problems(problems)

        for problem in problems:
            trigger_id = problem['objectid']

            if trigger_id in triggers:
                trigger = triggers[trigger_id]
            else:
                # This trigger is dependent on another or was disabled after the problem occurred
                continue

            if self._is_summary_trigger(trigger):
                # Skip summary problems
                continue

            event_id = problem['eventid']
            event_severity = self.ZABBIX_TO_UNIMON_SEVERITY[ int(trigger['priority']) ]
            event_object = trigger['hosts'][0]['name']
            event_text = trigger['description']

            if len(problem['tags']) != 0:
                event_text += ' [ '

                for tag in problem['tags']:
                    event_text += tag['tag']

                    if len(tag['value']) != 0:
                        event_text += ':' + tag['value']

                    event_text += ', '

                event_text = event_text[:-2] + ' ]'

            event = Event(Event.PROBLEM, True, event_severity, event_object, event_text, event_id)
            events.append(event)

        return events

    def get_summary(self, severities):
        object_groups = {}
        zabbix_severities = self._unimon_to_zabbix_severity(severities)
        problems = self._get_problems(zabbix_severities)
        triggers = self._get_triggers_by_problems(problems)

        for problem in problems:
            trigger_id = problem['objectid']

            if trigger_id in triggers:
                trigger = triggers[trigger_id]
            else:
                # This trigger is dependent on another or was disabled after the problem occurred
                continue

            if self._is_summary_trigger(trigger):
                # Skip summary problems
                continue

            for host_group in trigger['groups']:
                if self._is_summary_group(host_group):
                    # Skip summary groups
                    continue

                group_id = host_group['groupid']
                group_name = host_group['name']

                if group_id in object_groups:
                    # Get already created object
                    object_group = object_groups[group_id]
                else:
                    # Create new object
                    object_group = HostGroup(group_name, group_id)
                    object_groups[group_id] = object_group

                severity = self.ZABBIX_TO_UNIMON_SEVERITY[ int(trigger['priority']) ]
                object_group.count_problem(severity)

        return object_groups.values()

    def get_supported_agent_os(self):
        return self.SUPPORTED_AGENT_OS

    def install_agent(self, os_type, hostname, user, password):
        if not self._agent_repository:
            raise UnimonError('Install agent repository is not specified')

        if os_type == 'Windows' and self._agent_install_win:
            cmd = [ self._agent_install_win ]
        elif os_type == 'Linux' and self._agent_install_lin:
            cmd = [ self._agent_install_lin ]
        else:
            raise UnimonError('Usupported OS type "{0}"'.format(os_type))

        cmd += [
            self._agent_repository,
            hostname,
            user,
            password,
        ]

        process = subprocess.Popen(cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        timer = threading.Timer(self.INSTALL_AGENT_TIMEOUT_SEC, process.kill)

        try:
            timer.start()
            stdout, stderr = process.communicate()
        finally:
            timer.cancel()

        stderr = stderr.replace('\n', '\n\t').strip()

        if process.returncode == 0:
            self._log.info(stderr)
        else:
            self._log.error(stderr)

        return process.returncode

    def get_available_host_groups(self):
        host_groups = []
        all_groups = self._zabbix_api.hostgroup.get(output=['groupid', 'name'], filter={'flags': 0})
        template_groups = self._zabbix_api.hostgroup.get(output=['groupid'], templated_hosts=True)
        template_groups = [ group['groupid'] for group in template_groups ]

        # Filter out template groups
        for group in all_groups:
            if group['groupid'] not in template_groups:
                host_groups.append(group['name'])

        return host_groups

    def add_host(self, name, groups):
        group_ids = []
        template_ids = []

        for group in groups:
            group_id = self._get_group_id(group)
            if not group_id:
                raise UnimonError(u'Group "{}" is not found in Zabbix database'.format(group))

            template = self._match_filter + ' ' + group
            template_id = self._get_template_id(template, visible=False)
            if not template_id:
                # Try to find also by visible name
                template_id = self._get_template_id(template, visible=True)
                if not template_id:
                    raise UnimonError(u'Template "{}" is not found in Zabbix database'.format(template))

            group_ids.append({ 'groupid': group_id })
            template_ids.append({ 'templateid': template_id })

        # Check whether name is an IP address or hostname
        if re.search('^(\d{1,3}\.){3}\d{1,3}$', name):
            dns = ''
            ip = name
            use_ip = 1
        else:
            dns = name
            ip = ''
            use_ip = 0

        result = self._zabbix_api.host.create(
            host = name,
            interfaces = [{
                'type': 1,
                'main': 1,
                'useip': use_ip,
                'ip': ip,
                'dns': dns,
                'port': self.DEFAULT_ZABBIX_PORT,
            }],
            groups = group_ids,
            templates = template_ids,
        )
        return result['hostids'][0]

    def get_host_id(self, name, visible=False):
        return lookup.get_object_id(self._zabbix_api, name, lookup.HOST, visible)

    def get_host_name(self, id, visible=False):
        return lookup.get_object_name(self._zabbix_api, id, lookup.HOST, visible)

    def _get_group_id(self, name):
        return lookup.get_object_id(self._zabbix_api, name, lookup.HOST_GROUP)

    def _get_template_id(self, name, visible=False):
        return lookup.get_object_id(self._zabbix_api, name, lookup.TEMPLATE, visible)

    def delete_host(self, id):
        self._zabbix_api.host.delete(id)

    def export_config(self, auto_created=False):
        return export_configs(self._zabbix_api, auto_created)

    def import_config(self, config, overwrite=True, delete=False):
        import_configs(self._zabbix_api, config, overwrite, delete)
