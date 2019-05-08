import pytest
from unimonapi import HostGroup
from unimonapi import Event
from unimonapi import UnimonError

@pytest.fixture
def host_group():
    return HostGroup('name', 'id')

def test_host_group_init(host_group):
    assert host_group.name == 'name'
    assert host_group.id == 'id'
    assert host_group.severity == Event.NO_SEVERITY
    assert host_group.problems == 0
    assert host_group.problems_by_severity[Event.CRITICAL] == 0
    assert host_group.problems_by_severity[Event.WARNING] == 0
    assert host_group.problems_by_severity[Event.INFO] == 0

def test_host_group_unicode(host_group):
    host_group_unicode = unicode(host_group)
    assert host_group_unicode == u'name'
    host_group.severity = Event.CRITICAL
    host_group_unicode = unicode(host_group)
    assert host_group_unicode == u'\u26d4name'

def test_host_group_str(host_group):
    host_group_str = str(host_group)
    assert host_group_str == 'name'
    host_group.severity = Event.CRITICAL
    host_group_str = str(host_group)
    assert host_group_str == '\xe2\x9b\x94name'

def test_host_group_count_problem(host_group):
    host_group.count_problem(Event.CRITICAL)
    assert host_group.severity == Event.CRITICAL
    assert host_group.problems == 1
    assert host_group.problems_by_severity[Event.CRITICAL] == 1
    assert host_group.problems_by_severity[Event.WARNING] == 0
    assert host_group.problems_by_severity[Event.INFO] == 0

def test_host_group_count_problem_unsupported(host_group):
    with pytest.raises(UnimonError, match=r'Unsupported problem severity "unsupported"'):
        host_group.count_problem('unsupported')
