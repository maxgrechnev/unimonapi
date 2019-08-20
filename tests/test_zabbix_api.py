import pytest
from mock import patch
from mock import call
from mock import MagicMock
from unimonapi import MonitoringAPI
from unimonapi import ZabbixAPI
from unimonapi import UnimonError
from unimonapi import Event
from unimonapi import HostGroup

@pytest.fixture(scope='module')
@patch('unimonapi.zabbix.zabbix_api.PyZabbixAPI')
def zabbix_api(mock):
    zabbix_api = ZabbixAPI('http://zabbix-frontend', 'Admin', 'zabbix123', '/path/to/repo', 'install_win.sh', 'install_lin.sh', 'match_filter')
    zabbix_api.mock = mock
    zabbix_api.mock_instance = mock.return_value
    return zabbix_api

def test_zabbix_api_init(zabbix_api):
    assert isinstance(zabbix_api, MonitoringAPI)
    zabbix_api.mock.assert_called_once_with('http://zabbix-frontend')
    zabbix_api.mock_instance.login.assert_called_once_with('Admin', 'zabbix123')

@pytest.mark.parametrize('rules_number', [1, 5, pytest.param(0, marks=pytest.mark.xfail(raises=UnimonError))])
def test_zabbix_api_get_discovery_ip_range(zabbix_api, rules_number):
    zabbix_api.mock_instance.drule.get = MagicMock()
    zabbix_api.mock_instance.drule.get.return_value = rules_number * [{
        'druleid': 'rule_id',
        'iprange': '1.1.1.1',
    }]

    returned_ip_range = zabbix_api.get_discovery_ip_range()

    zabbix_api.mock_instance.drule.get.assert_called_once()
    assert returned_ip_range == '1.1.1.1'

@pytest.mark.parametrize('rules_number', [1, 5, pytest.param(0, marks=pytest.mark.xfail(raises=UnimonError))])
def test_zabbix_api_start_default_discovery(zabbix_api, rules_number):
    zabbix_api.mock_instance.drule.get = MagicMock()
    zabbix_api.mock_instance.drule.update = MagicMock()
    zabbix_api.mock_instance.drule.get.return_value = rules_number * [{
        'druleid': 'rule_id',
    }]

    zabbix_api.start_discovery()

    zabbix_api.mock_instance.drule.get.assert_called_once()
    assert zabbix_api.mock_instance.drule.update.call_count == rules_number
    update_calls = [call(druleid='rule_id', status=0)] * rules_number
    zabbix_api.mock_instance.drule.update.assert_has_calls(update_calls)

def test_zabbix_api_start_discovery_with_ip_range(zabbix_api):
    zabbix_api.mock_instance.drule.get = MagicMock()
    zabbix_api.mock_instance.drule.update = MagicMock()
    zabbix_api.mock_instance.drule.get.return_value = [{
        'druleid': 'rule_id',
    }]

    zabbix_api.start_discovery('1.1.1.1')

    zabbix_api.mock_instance.drule.get.assert_called_once()
    zabbix_api.mock_instance.drule.update.assert_called_once_with(druleid='rule_id', iprange='1.1.1.1', status=0)

@pytest.mark.parametrize('rules_number', [1, 5, pytest.param(0, marks=pytest.mark.xfail(raises=UnimonError))])
def test_zabbix_api_stop_discovery(zabbix_api, rules_number):
    zabbix_api.mock_instance.drule.get = MagicMock()
    zabbix_api.mock_instance.drule.update = MagicMock()
    zabbix_api.mock_instance.drule.get.return_value = rules_number * [{
        'druleid': 'rule_id',
    }]

    zabbix_api.stop_discovery()

    zabbix_api.mock_instance.drule.get.assert_called_once()
    assert zabbix_api.mock_instance.drule.update.call_count == rules_number
    update_calls = [call(druleid='rule_id', status=1)] * rules_number
    zabbix_api.mock_instance.drule.update.assert_has_calls(update_calls)

@pytest.mark.parametrize('problems_number', [1, 5])
def test_get_problems(zabbix_api, problems_number):
    zabbix_api.mock_instance.problem.get = MagicMock()
    zabbix_api.mock_instance.trigger.get = MagicMock()
    zabbix_api.mock_instance.problem.get.return_value = problems_number * [{
        'eventid': 'event_id',
        'objectid': 'trigger_id',
        'tags': [],
    }]
    zabbix_api.mock_instance.trigger.get.return_value = {
        'trigger_id': {
            'triggerid': 'trigger_id',
            'description': 'High CPU usage',
            'priority': 1,
            'hosts': [{
                'hostid': 'host_id',
                'name': 'zabbix-server',
            }],
            'groups': [{
                'groupid': 'group_id',
                'name': 'Zabbix Servers',
            }],
        }
    }

    problems = zabbix_api.get_problems()

    zabbix_api.mock_instance.problem.get.assert_called_once()
    zabbix_api.mock_instance.trigger.get.assert_called()
    assert len(problems) == problems_number
    assert isinstance(problems[0], Event)
    assert problems[0].type == Event.PROBLEM
    assert problems[0].detailed
    assert problems[0].severity == Event.INFO
    assert problems[0].host == 'zabbix-server'
    assert problems[0].text == 'High CPU usage'
    assert problems[0].id == 'event_id'

@pytest.mark.parametrize(
    ('priority', 'severity'),
    [
        (1, Event.INFO),
        (2, Event.WARNING),
        (4, Event.CRITICAL)
    ],
)
def test_get_problems_with_priority(zabbix_api, priority, severity):
    zabbix_api.mock_instance.problem.get.return_value = [{
        'eventid': 'event_id',
        'objectid': 'trigger_id',
        'tags': [],
    }]
    zabbix_api.mock_instance.trigger.get.return_value = {
        'trigger_id': {
            'triggerid': 'trigger_id',
            'description': 'High CPU usage',
            'priority': priority,
            'hosts': [{
                'hostid': 'host_id',
                'name': 'zabbix-server',
            }],
            'groups': [{
                'groupid': 'group_id',
                'name': 'Zabbix Servers',
            }],
        }
    }

    problems = zabbix_api.get_problems()

    assert len(problems) == 1
    assert problems[0].severity == severity

@pytest.mark.parametrize(
    ('tags_number', 'tag', 'tag_value', 'tag_string'),
    [
        (0, 'App', 'Zabbix', ''),
        (1, 'App', '', ' [ App ]'),
        (1, 'App', 'Zabbix', ' [ App:Zabbix ]'),
        (3, 'App', '', ' [ App, App, App ]'),
    ],
)
def test_get_problems_with_tags(zabbix_api, tags_number, tag, tag_value, tag_string):
    zabbix_api.mock_instance.problem.get.return_value = [{
        'eventid': 'event_id',
        'objectid': 'trigger_id',
        'tags': tags_number * [{
            'tag': tag,
            'value': tag_value,
        }],
    }]
    zabbix_api.mock_instance.trigger.get.return_value = {
        'trigger_id': {
            'triggerid': 'trigger_id',
            'description': 'High CPU usage',
            'priority': 1,
            'hosts': [{
                'hostid': 'host_id',
                'name': 'zabbix-server',
            }],
            'groups': [{
                'groupid': 'group_id',
                'name': 'Zabbix Servers',
            }],
        }
    }

    problems = zabbix_api.get_problems()

    assert len(problems) == 1
    assert problems[0].text == 'High CPU usage' + tag_string

@pytest.mark.parametrize(
    ('severities', 'priorities'),
    [
        ([Event.CRITICAL], [4,5]),
        ([Event.INFO, Event.WARNING], [0,1,2,3]),
        (None, [0,1,2,3,4,5]),
        ([], []),
        ('abcd', []),
        ([99,555], []),
        pytest.param(123, [], marks=pytest.mark.xfail(raises=TypeError)),
    ],
)
def test_get_problems_with_severity(zabbix_api, severities, priorities):
    zabbix_api.mock_instance.problem.get.return_value = []
    zabbix_api.mock_instance.trigger.get.return_value = {}

    zabbix_api.get_problems(severities=severities)

    args, kwargs = zabbix_api.mock_instance.problem.get.call_args
    assert 'severities' in kwargs
    assert kwargs['severities'] == priorities

def test_get_problems_with_groups(zabbix_api):
    zabbix_api.mock_instance.problem.get.return_value = []
    zabbix_api.mock_instance.trigger.get.return_value = {}

    zabbix_api.get_problems(groups=['id_1', 'id_2'])

    args, kwargs = zabbix_api.mock_instance.problem.get.call_args
    assert 'groupids' in kwargs
    assert kwargs['groupids'] == ['id_1', 'id_2']

def test_get_problems_dependent(zabbix_api):
    zabbix_api.mock_instance.problem.get.return_value = [{
        'eventid': 'event_id',
        'objectid': 'trigger_id',
        'tags': [],
    }]
    zabbix_api.mock_instance.trigger.get.return_value = {}

    problems = zabbix_api.get_problems()

    args, kwargs = zabbix_api.mock_instance.trigger.get.call_args
    assert 'monitored' in kwargs
    assert kwargs['monitored'] == 1
    assert 'skipDependent' in kwargs
    assert kwargs['skipDependent'] == 1
    assert len(problems) == 0

def test_get_summary(zabbix_api):
    zabbix_api.mock_instance.problem.get = MagicMock()
    zabbix_api.mock_instance.trigger.get = MagicMock()
    zabbix_api.mock_instance.problem.get.return_value = [
        {
            'eventid': 'critical_event_id',
            'objectid': 'critical_trigger_id',
        },
        {
            'eventid': 'warning_event_id',
            'objectid': 'warning_trigger_id',
        },
    ]
    zabbix_api.mock_instance.trigger.get.return_value = {
        'critical_trigger_id': {
            'triggerid': 'critical_trigger_id',
            'priority': 5,
            'groups': [
                {
                    'groupid': 'group_id_1',
                    'name': 'Group 1',
                },
                {
                    'groupid': 'group_id_2',
                    'name': 'Group 2',
                },
            ],
        },
        'warning_trigger_id': {
            'triggerid': 'warning_trigger_id',
            'priority': 3,
            'groups': [{
                'groupid': 'group_id_1',
                'name': 'Group 1',
            }],
        }
    }

    host_groups = zabbix_api.get_summary([Event.CRITICAL, Event.WARNING])

    zabbix_api.mock_instance.problem.get.assert_called_once()
    zabbix_api.mock_instance.trigger.get.assert_called()
    assert len(host_groups) == 2
    assert host_groups[0].id == 'group_id_1'
    assert host_groups[0].severity == Event.CRITICAL
    assert host_groups[0].problems == 2
    assert host_groups[1].id == 'group_id_2'
    assert host_groups[1].severity == Event.CRITICAL
    assert host_groups[1].problems == 1

@pytest.mark.parametrize(
    ('os_type', 'bin_file'),
    [
        ('Windows', 'install_win.sh'),
        ('Linux', 'install_lin.sh'),
        pytest.param('Android', '', marks=pytest.mark.xfail(raises=UnimonError)),
    ],
)
def test_install_agent(zabbix_api, os_type, bin_file):
    with patch('subprocess.Popen') as MockPopen:
        MockPopen.return_value.communicate.return_value = ('stdout', 'stderr')
        MockPopen.return_value.returncode = 777
        
        return_code = zabbix_api.install_agent(os_type, 'my-host', 'root', '12345')
        
        MockPopen.assert_called_once()
        args, kwargs = MockPopen.call_args
        assert args[0] == [bin_file, '/path/to/repo', 'my-host', 'root', '12345']
        assert return_code == 777

def test_get_available_host_groups(zabbix_api):
    zabbix_api.mock_instance.hostgroup.get = MagicMock()
    zabbix_api.mock_instance.hostgroup.get.side_effect = (
        [
            {
                'groupid': 'group_id_1',
                'name': 'Host group',
            },
            {
                'groupid': 'group_id_2',
                'name': 'Template group',
            }
        ],
        [
            {
                'groupid': 'group_id_2',
                'name': 'Template group',
            }
        ],
    )

    returned_groups = zabbix_api.get_available_host_groups()

    assert zabbix_api.mock_instance.hostgroup.get.call_count == 2
    assert returned_groups == ['Host group']

@pytest.mark.parametrize(
    ('host_name', 'use_ip', 'ip', 'dns'),
    [
        ('new-host', 0, '', 'new-host'),
        ('1.1.1.1', 1, '1.1.1.1', ''),
    ],
)
def test_add_host(zabbix_api, host_name, use_ip, ip, dns):
    zabbix_api.mock_instance.hostgroup.get = MagicMock()
    zabbix_api.mock_instance.template.get = MagicMock()
    zabbix_api.mock_instance.host.create = MagicMock()
    zabbix_api.mock_instance.hostgroup.get.return_value = [{'groupid': 'group_id'}]
    zabbix_api.mock_instance.template.get.return_value = [{'templateid': 'template_id'}]
    zabbix_api.mock_instance.host.create.return_value = {'hostids': ['new_host_id']}

    returned_host_id = zabbix_api.add_host(host_name, ['Host group'])

    zabbix_api.mock_instance.hostgroup.get.assert_called_once()
    zabbix_api.mock_instance.template.get.assert_called_once()
    args, kwargs = zabbix_api.mock_instance.template.get.call_args
    assert kwargs['filter'] == {'host': 'match_filter Host group'}
    zabbix_api.mock_instance.host.create.assert_called_once()
    args, kwargs = zabbix_api.mock_instance.host.create.call_args
    assert kwargs['host'] == host_name
    assert kwargs['groups'] == [{'groupid': 'group_id'}]
    assert kwargs['templates'] == [{'templateid': 'template_id'}]
    assert kwargs['interfaces'][0]['useip'] == use_ip
    assert kwargs['interfaces'][0]['ip'] == ip
    assert kwargs['interfaces'][0]['dns'] == dns
    assert returned_host_id == 'new_host_id'

def test_delete_host(zabbix_api):
    zabbix_api.mock_instance.host.delete = MagicMock()
    zabbix_api.delete_host('host_id')
    zabbix_api.mock_instance.host.delete.assert_called_once_with('host_id')

def test_get_host_id(zabbix_api):
    zabbix_api.mock_instance.host.get = MagicMock()
    zabbix_api.mock_instance.host.get.return_value = [{'hostid': 'host_id'}]

    returned_id = zabbix_api.get_host_id('my-host')

    zabbix_api.mock_instance.host.get.assert_called_once()
    assert returned_id == 'host_id'

def test_get_host_name(zabbix_api):
    zabbix_api.mock_instance.host.get = MagicMock()
    zabbix_api.mock_instance.host.get.return_value = [{
        'hostid': 'host_id',
        'host': 'my-host',
    }]

    returned_name = zabbix_api.get_host_name('host_id')

    zabbix_api.mock_instance.host.get.assert_called_once()
    assert returned_name == 'my-host'

# def test_export_config(zabbix_api):
    # zabbix_api.mock_instance.configuration.export = MagicMock()
    # zabbix_api.mock_instance.template.get = MagicMock()
    # zabbix_api.mock_instance.host.get = MagicMock()
    # zabbix_api.mock_instance.valuemap.get = MagicMock()
    # zabbix_api.mock_instance.hostgroup.get = MagicMock()
    # zabbix_api.mock_instance.usermacro.get = MagicMock()
    # zabbix_api.mock_instance.drule.get = MagicMock()
    # zabbix_api.mock_instance.action.get = MagicMock()
    # zabbix_api.mock_instance.template.get.return_value = { 'template_id': { 'templateid': 'template_id' }}
    # zabbix_api.mock_instance.host.get.return_value = { 'host_id': { 'hostid': 'host_id' }}
    # zabbix_api.mock_instance.valuemap.get.return_value = { 'valuemap_id': { 'valuemapid': 'valuemap_id' }}
    # zabbix_api.mock_instance.hostgroup.get.return_value = { 'group_id': { 'groupid': 'group_id' }}
    # zabbix_api.mock_instance.configuration.export.return_value = {
        # 'zabbix_export': {
            # 'templates': [
            # ],
            # 'triggers': [
            # ],
            # 'value_maps': [
            # ],
            # 'hosts': [
            # ],
            # 'graphs': [
            # ],
            # 'version': [
            # ],
            # 'groups': [
            # ],
            
        # }
    # }

    # zabbix_api.export_config()

    # zabbix_api.mock_instance.host.delete.assert_called_once_with('host_id')
